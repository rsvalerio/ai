# SHOP rules

Shopify as the commerce backend of a Lovable app: the Storefront API (GraphQL) for catalogue,
cart and checkout, called from the browser or from an Edge Function, and the Admin API called only
from Edge Functions. Lovable's Shopify integration scaffolds this layer. Grounded in the Shopify
Storefront API reference (authentication, status codes, Cart API) and the Shopify API versioning
docs.

The Supabase rules still apply to the same app. A Shopify-backed Lovable app usually keeps its
catalogue and orders in Shopify and only its users, preferences and app tables in Supabase.

## Credentials (typical severity: Critical)

**Detection heuristics** — search for: `X-Shopify-Storefront-Access-Token`,
`Shopify-Storefront-Private-Token`, `X-Shopify-Access-Token`, `shpat_` / `shpss_` / `shppa_` /
`shpca_`, `myshopify.com/admin/api`, `SHOPIFY_` in `src/` or in a `VITE_*` variable.

- **SHOP-1.** Only the **public** Storefront access token reaches the browser. Shopify designs it
  for client use ("used to query the API from a browser or mobile app, where the token is visible
  to buyers") and sends it as `X-Shopify-Storefront-Access-Token`. A public token hardcoded in
  `src/lib/shopify.ts` is **not** a leak, and neither `code-review-web` SEC-10 nor this rule is
  filed for it. These are leaks, and each one is Critical: a **private** Storefront token
  (`Shopify-Storefront-Private-Token`), an Admin API token (`X-Shopify-Access-Token`, `shpat_…`),
  an app's API secret (`shpss_…`), or a legacy private-app password (`shppa_…`) anywhere under
  `src/`, in a `VITE_*` variable or in `index.html`. Those belong in a Supabase secret, read by an
  Edge Function (EDGE-7). Lovable may also route Storefront calls through an Edge Function with the
  token in Cloud secrets. Both setups are correct, so judge the token's class, not where it sits.
  A server-side Storefront call made for a buyer forwards `Shopify-Storefront-Buyer-IP`, or Shopify
  rate-limits every buyer as one client.
  — shopify.dev/docs/api/storefront#authentication

## Request handling (typical severity: High)

**Detection heuristics** — search for: the Storefront request helper (`storefrontApiRequest`,
`fetch(` to `graphql.json`); `.errors` without `userErrors`; `return;` or `return null` inside a
`queryFn`; `cartCreate` / `cartLinesAdd` / `cartLinesUpdate` / `cartLinesRemove` /
`cartDiscountCodesUpdate` results read without `userErrors`.

- **SHOP-2.** Read both error channels. GraphQL returns `200 OK` for failures REST would answer
  with a 4xx, carrying top-level `errors` (`THROTTLED`, `ACCESS_DENIED`, `SHOP_INACTIVE`). Every
  mutation also returns a `userErrors` list (a sold-out variant, an invalid discount code, a gift
  card recipient Shopify rejects) next to a possibly non-null payload. A helper that checks only
  `response.ok`, or only `errors`, reports a failed cart change as a success. The non-200 codes
  have their own meaning: `402` means the shop is frozen (often an unclaimed or unpaid Lovable
  store), `403` a store flagged as fraudulent, and `430` a request Shopify judged malicious. Inside
  TanStack Query, the helper **throws** on all of them (QRY-2). Returning `undefined` from a
  `queryFn` is itself an error in v5, and swapping a toast in for the throw hides the failure from
  `isError`.
  — shopify.dev/docs/api/storefront#status-and-error-codes

## Money (typical severity: High)

**Detection heuristics** — search for: `price *` / `* (1 -` / `DISCOUNT` constants in
`src/`; `subscription` / `subscribe` UI without `sellingPlan`; `parseFloat(…amount)` rendered with
a hardcoded currency symbol.

- **SHOP-3.** The price the UI shows is the price checkout charges. Prices, compare-at prices and
  totals come from Shopify (`price`, `compareAtPrice`, `cart.cost`), and every saving the UI
  promises is one Shopify applies: a selling plan for subscriptions (`sellingPlanId` on the cart
  line, with the product in a selling plan group), an automatic discount, or a code applied to the
  cart (`cartDiscountCodesUpdate`). A client-side `SUBSCRIPTION_DISCOUNT = 0.1` multiplied into the
  displayed price while the cart line carries no selling plan advertises a price the buyer is not
  charged. That misrepresents the price, so file it **High**, not as a display bug. Format money
  from `amount` with its `currencyCode` (`Intl.NumberFormat`), not a hardcoded symbol.
  — shopify.dev/docs/api/storefront/latest/objects/SellingPlan

## Cart & versioning (typical severity: Medium)

- **SHOP-4.** The Shopify cart is the source of truth, and the local copy is a cache of it. A
  persisted `cartId` / `checkoutUrl` (a Zustand `persist` store, see QRY-7) is revalidated
  against the `cart` query on load. A `null` cart (expired, or already checked out) clears the
  local state rather than letting `cartLinesAdd` fail against it. Local line items are rebuilt from
  the returned cart after every mutation, not patched optimistically and left to drift. The buyer
  is sent to the `checkoutUrl` Shopify returned: adding a query parameter is fine, rebuilding the
  host or path is not. Clear the cart only once checkout is confirmed, not when the checkout tab
  opens.
  — shopify.dev/docs/api/storefront/latest/objects/Cart
- **SHOP-5.** The API version lives in one constant and is inside Shopify's support window. Each
  stable version is supported for at least 12 months, and a request to a retired version does
  **not** fail: Shopify "falls forward and responds using the oldest accessible stable version",
  so behaviour changes underneath an unchanged app. Lovable pins the version current when the
  integration was added (`2025-07` in 2025 projects), in the browser helper and again in each Edge
  Function. File one finding listing every pin. A version more than 12 months old is past its
  minimum support. Pins that disagree with each other are a finding even when both are supported.
  *(Typical severity: Medium; Low while the version is still in support.)*
  — shopify.dev/docs/api/usage/versioning
