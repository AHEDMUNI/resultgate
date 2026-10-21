# Commercial and processor qualification — 2026-10-21

This is a reviewed-source shortlist, not an enrolled provider list. No new messages sent.

## Fastest bounded route

Start with one independent provider who owns a low-risk service (e.g. public-data
format conversion or analysis), accepts the 5% contract, and can pass Stripe onboarding.
This avoids assuming resale rights to a SaaS subscription. The provider still has to
be recruited/qualified; no current buyer or provider acceptance is proved.

Apify's official partner directory explicitly supports solution experts, integrations
and independent Actor creators. It is a relevant source of potential providers;
no general right to resell every Actor or collect its price is implied.
Sources: https://apify.com/partners and https://apify.com/partners/join
Independent creators can be approached for an explicit listing/collection agreement
only after outreach approval. Their own IP/licensing and platform terms require review.
The public affiliate commission is a different model, NOT our chosen 5% marketplace.

BrowserAct/Firecrawl/ScraperAPI inquiries previously concerned referrals. A referral
reply does not authorize marketplace collection, a 5% split, account resale or payment
on their behalf. They must not be listed as contracted providers under this new model.
PR #11's Firecrawl-specific plan and varying commissions do not govern this module.

## Stripe sources and decision

- https://docs.stripe.com/connect/destination-charges.md?platform=web&ui=stripe-hosted
  Hosted Checkout supports application fee and destination account. Destination charges
  debit platform for processing/refunds/disputes; default refund behavior needs explicit
  transfer and application-fee reversal. Test adapter follows this shape, not direct transfers.
- https://stripe.com/connect/pricing
  US published platform-managed pricing: $2/month per active payout account plus
  0.25% + $0.25 per payout. Card processing starts at 2.9% + $0.30. Account configuration,
  country, payment method and negotiated terms can differ. Costs not accepted here.
- https://docs.stripe.com/connect/marketplace
  Marketplace responsibilities include fees, risk and negative balances. Stripe
  onboarding does not eliminate the platform's contractual responsibilities.
- https://docs.stripe.com/connect/cross-border-payouts
  Cross-border eligibility is restricted. Pilot intentionally limits test accounts to
  US and USD; this does not certify AHED/ALLUBI/ResultGate account eligibility.
- https://docs.stripe.com/events/manage-webhook-endpoints
  Signature verification uses the unchanged raw body; duplicate and out-of-order events
  must be expected. No success-page-based commission booking.

Illustrative economics, not a transaction: on $100, gross 5% is $5. At the published
starting card rate, $3.20 processing would leave $1.80 before Connect/payout costs,
refunds, disputes and taxes if the platform bears those fees. We have not approved a
surcharge or shifted fees to a provider. Final cost allocation requires explicit agreement.

## Outstanding evidence

No Stripe test secrets configured in this Work environment. No actual Stripe sandbox
session or card payment was executed. Public documentation does not establish account
approval. Identity, beneficial ownership and bank details must be entered by the owner
through Stripe's hosted flow, never shared in chat. Live provider agreements and final
terms are pending. No account creation, agreement signature or financial commitment.
