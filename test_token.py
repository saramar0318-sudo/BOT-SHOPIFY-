import shopify

session = shopify.Session("openboxsv.myshopify.com", "2024-10", "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")
shopify.ShopifyResource.activate_session(session)

shop = shopify.Shop.current()
print(shop.name)
