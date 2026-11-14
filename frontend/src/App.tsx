import { useEffect, useMemo, useState } from "react";

type Product = {
  id: number;
  boutique_id: number;
  boutique: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  stock_quantity: number;
};

type Boutique = {
  id: number;
  name: string;
  integration_type: string;
};

type CartItem = {
  product: Product;
  quantity: number;
};

type Order = {
  id: number;
  total_amount: number;
  currency: string;
};

const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

function messageFromError(error: unknown): string {
  return error instanceof Error ? error.message : "An unexpected error occurred.";
}

async function responseError(response: Response): Promise<Error> {
  const body: unknown = await response.json().catch(() => null);
  if (
    typeof body === "object" &&
    body !== null &&
    "detail" in body &&
    typeof body.detail === "string"
  ) {
    return new Error(body.detail);
  }
  return new Error(`Request failed (${response.status}).`);
}

function formatPrice(price: number, currency: string): string {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency,
  }).format(price);
}

export default function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [boutiques, setBoutiques] = useState<Boutique[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [query, setQuery] = useState("");
  const [boutiqueId, setBoutiqueId] = useState("");
  const [stockOnly, setStockOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [boutiquesError, setBoutiquesError] = useState("");
  const [catalogueError, setCatalogueError] = useState("");
  const [cartError, setCartError] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState("");
  const [checkoutInProgress, setCheckoutInProgress] = useState(false);
  const [order, setOrder] = useState<Order | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_URL}/api/boutiques`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw await responseError(response);
        return (await response.json()) as Boutique[];
      })
      .then(setBoutiques)
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setBoutiquesError(messageFromError(error));
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams();
    if (query.trim()) params.set("q", query.trim());
    if (boutiqueId) params.set("boutique_id", boutiqueId);
    if (stockOnly) params.set("stock_only", "true");
    const search = params.size > 0 ? `?${params.toString()}` : "";

    setLoading(true);
    setCatalogueError("");
    fetch(`${API_URL}/api/products${search}`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw await responseError(response);
        return (await response.json()) as Product[];
      })
      .then(setProducts)
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setCatalogueError(messageFromError(error));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [query, boutiqueId, stockOnly, reloadKey]);

  const cartTotal = useMemo(
    () =>
      cart.reduce(
        (total, item) => total + item.product.price * item.quantity,
        0,
      ),
    [cart],
  );
  const cartCurrency = cart[0]?.product.currency ?? "EUR";
  const cartCount = cart.reduce((total, item) => total + item.quantity, 0);

  function addToCart(product: Product) {
    setOrder(null);
    setCartError("");
    setCart((current) => {
      const existing = current.find((item) => item.product.id === product.id);
      if (existing) {
        return current.map((item) =>
          item.product.id === product.id
            ? {
                ...item,
                product,
                quantity: Math.min(item.quantity + 1, product.stock_quantity),
              }
            : item,
        );
      }
      return [...current, { product, quantity: 1 }];
    });
  }

  function changeQuantity(productId: number, quantity: number) {
    setCart((current) =>
      quantity < 1
        ? current.filter((item) => item.product.id !== productId)
        : current.map((item) =>
            item.product.id === productId
              ? {
                  ...item,
                  quantity: Math.min(quantity, item.product.stock_quantity),
                }
              : item,
          ),
    );
  }

  async function syncCatalogues() {
    setSyncing(true);
    setSyncMessage("");
    setCatalogueError("");
    try {
      const results = await Promise.all(
        boutiques.map(async (boutique) => {
          const response = await fetch(
            `${API_URL}/api/admin/boutiques/${boutique.id}/catalogue-sync`,
            { method: "POST" },
          );
          if (!response.ok) throw await responseError(response);
          return response.json();
        }),
      );
      const received = results.reduce(
        (total: number, result: { received: number }) =>
          total + result.received,
        0,
      );
      setSyncMessage(`Synced ${received} products from ${boutiques.length} boutiques.`);
      setReloadKey((key) => key + 1);
    } catch (error: unknown) {
      setCatalogueError(`Catalogue sync failed: ${messageFromError(error)}`);
    } finally {
      setSyncing(false);
    }
  }

  async function checkout() {
    setCheckoutInProgress(true);
    setCartError("");
    try {
      const response = await fetch(`${API_URL}/api/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: cart.map(({ product, quantity }) => ({
            product_id: product.id,
            quantity,
          })),
        }),
      });
      if (!response.ok) throw await responseError(response);
      const completedOrder = (await response.json()) as Order;
      setOrder(completedOrder);
      setCart([]);
      setReloadKey((key) => key + 1);
    } catch (error: unknown) {
      setCartError(messageFromError(error));
    } finally {
      setCheckoutInProgress(false);
    }
  }

  const hasFilters = Boolean(query || boutiqueId || stockOnly);

  return (
    <main className="page">
      <header className="topbar">
        <a className="brand" href="/" aria-label="SmartShop home">
          <span className="brand-mark">S</span>
          <span>smartshop</span>
        </a>
        <span className="topbar-note">Independent finds, together</span>
        <button
          className="cart-toggle"
          type="button"
          aria-label={`Shopping bag, ${cartCount} items`}
          onClick={() => document.getElementById("shopping-bag")?.scrollIntoView({ behavior: "smooth" })}
        >
          Bag <span>{cartCount}</span>
        </button>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">A LITTLE MORE LOCAL</p>
          <h1>Good things,<br />all in one place.</h1>
          <p className="hero-description">
            Explore considered pieces from independent boutiques. Find your
            next favourite, without the endless scroll.
          </p>
          <a className="hero-link" href="#catalogue">Explore the collection <span aria-hidden="true">↓</span></a>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="sun"></div>
          <div className="arch">
            <div className="arch-shape"></div>
            <div className="arch-shelf"></div>
            <div className="vase vase-one"></div>
            <div className="vase vase-two"></div>
          </div>
          <span className="hero-caption">CURATED FOR EVERYDAY</span>
        </div>
        <div className="hero-index">01 <span>—</span> 02</div>
      </section>

      <section className="collection" id="catalogue">
        <div className="collection-intro">
          <div>
            <p className="eyebrow">THE SMARTSHOP EDIT</p>
            <h2>Find your new favourite.</h2>
          </div>
          <p className="collection-note">Thoughtful finds from boutiques worth knowing.</p>
        </div>

        <div className="catalogue-tools">
          <label className="search-field">
            <span className="search-icon" aria-hidden="true">⌕</span>
            <span className="visually-hidden">Search products</span>
            <input
              type="search"
              placeholder="Search the collection"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          <label className="select-field">
            <span className="visually-hidden">Filter by boutique</span>
            <select value={boutiqueId} onChange={(event) => setBoutiqueId(event.target.value)}>
              <option value="">All boutiques</option>
              {boutiques.map((boutique) => (
                <option key={boutique.id} value={boutique.id}>{boutique.name}</option>
              ))}
            </select>
          </label>
          <label className="stock-filter">
            <input
              type="checkbox"
              checked={stockOnly}
              onChange={(event) => setStockOnly(event.target.checked)}
            />
            <span>In stock</span>
          </label>
          <button
            className="sync-button"
            type="button"
            onClick={syncCatalogues}
            disabled={syncing || boutiques.length === 0}
          >
            {syncing ? "Syncing…" : "↻ Sync catalogues"}
          </button>
        </div>

        {boutiquesError && <p className="notice error-notice" role="alert">Boutiques unavailable: {boutiquesError}</p>}
        {catalogueError && <p className="notice error-notice" role="alert">{catalogueError}</p>}
        {syncMessage && <p className="notice success-notice" role="status">{syncMessage}</p>}
        {order && (
          <div className="order-confirmation" role="status">
            <span className="confirmation-check">✓</span>
            <div>
              <strong>Order #{order.id} is confirmed.</strong>
              <span>Demo checkout complete · {formatPrice(order.total_amount, order.currency)}</span>
            </div>
            <button type="button" onClick={() => setOrder(null)} aria-label="Dismiss confirmation">×</button>
          </div>
        )}

        <div className="results-bar">
          <span>{loading ? "Finding pieces…" : `${products.length} ${products.length === 1 ? "piece" : "pieces"}`}</span>
          {hasFilters && (
            <button
              className="clear-filters"
              type="button"
              onClick={() => {
                setQuery("");
                setBoutiqueId("");
                setStockOnly(false);
              }}
            >
              Clear filters
            </button>
          )}
        </div>

        {loading ? (
          <div className="empty-state" role="status">
            <span className="loader" aria-hidden="true"></span>
            <p>Gathering the good things…</p>
          </div>
        ) : products.length > 0 ? (
          <div className="product-grid">
            {products.map((product, index) => (
              <article className="product-card" key={product.id}>
                <div className={`product-art product-art-${index % 4}`} aria-hidden="true">
                  <span>{product.name.slice(0, 1)}</span>
                  <small>{product.boutique}</small>
                  {product.stock_quantity === 0 && <span className="sold-out">SOLD OUT</span>}
                </div>
                <div className="product-meta">
                  <span>{product.boutique}</span>
                  <span className={product.stock_quantity > 0 ? "in-stock" : "out-of-stock"}>
                    {product.stock_quantity > 0 ? "Available" : "Sold out"}
                  </span>
                </div>
                <h3>{product.name}</h3>
                <p className="product-description">{product.description}</p>
                <div className="product-bottom">
                  <strong>{formatPrice(product.price, product.currency)}</strong>
                  <button
                    className="add-button"
                    type="button"
                    onClick={() => addToCart(product)}
                    disabled={product.stock_quantity === 0}
                  >
                    {product.stock_quantity === 0 ? "Unavailable" : "Add to bag"}
                  </button>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <span className="empty-icon" aria-hidden="true">✳</span>
            <h3>No pieces found just yet.</h3>
            <p>Try another search or clear your filters to see everything.</p>
            {hasFilters && (
              <button
                className="text-button"
                type="button"
                onClick={() => {
                  setQuery("");
                  setBoutiqueId("");
                  setStockOnly(false);
                }}
              >
                Show the whole collection
              </button>
            )}
          </div>
        )}
      </section>

      <section className="bag-section" id="shopping-bag">
        <div className="bag-heading">
          <div>
            <p className="eyebrow">YOUR EDIT</p>
            <h2>Shopping bag <span>{cartCount}</span></h2>
          </div>
          {cart.length > 0 && (
            <button className="text-button" type="button" onClick={() => setCart([])}>Clear bag</button>
          )}
        </div>
        {cart.length === 0 ? (
          <p className="bag-empty">Your bag is waiting for something lovely.</p>
        ) : (
          <>
            <div className="bag-items">
              {cart.map(({ product, quantity }) => (
                <article className="bag-item" key={product.id}>
                  <div className="bag-item-art" aria-hidden="true">{product.name.slice(0, 1)}</div>
                  <div className="bag-item-info">
                    <span>{product.boutique}</span>
                    <strong>{product.name}</strong>
                    <span>{formatPrice(product.price, product.currency)}</span>
                  </div>
                  <div className="quantity-control" aria-label={`Quantity for ${product.name}`}>
                    <button
                      type="button"
                      onClick={() => changeQuantity(product.id, quantity - 1)}
                      aria-label={`Remove one ${product.name}`}
                    >−</button>
                    <span>{quantity}</span>
                    <button
                      type="button"
                      onClick={() => changeQuantity(product.id, quantity + 1)}
                      disabled={quantity >= product.stock_quantity}
                      aria-label={`Add one ${product.name}`}
                    >+</button>
                  </div>
                  <strong className="line-total">{formatPrice(product.price * quantity, product.currency)}</strong>
                </article>
              ))}
            </div>
            <div className="bag-summary">
              <p><span>Subtotal</span><strong>{formatPrice(cartTotal, cartCurrency)}</strong></p>
              <span className="checkout-note">Demo checkout · no payment details required</span>
              {cartError && <p className="notice error-notice" role="alert">{cartError}</p>}
              <button
                className="checkout-button"
                type="button"
                onClick={checkout}
                disabled={checkoutInProgress}
              >
                {checkoutInProgress ? "Placing order…" : "Place demo order"}
              </button>
            </div>
          </>
        )}
      </section>

      <footer className="footer">
        <a className="brand" href="/" aria-label="SmartShop home">
          <span className="brand-mark">S</span>
          <span>smartshop</span>
        </a>
        <p>Better finds. Independent minds.</p>
        <span>DEMO STORE · MADE FOR DISCOVERY</span>
      </footer>
    </main>
  );
}
