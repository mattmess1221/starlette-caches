# Caching Rules

In [`CacheMiddleware`][starlette_caches.middleware.CacheMiddleware], the `rules` argument is used to customize which endpoints get cached. It is a sequence of [`Rule`][starlette_caches.rules.Rule] objects defining a request path, a response status code, and the cache TTL.

Rules will be processed in order, using the first matching rule. If no rule matches, the response will not be cached.

To restore the default behavior after adding a rule, add a rule with default arguments to the end of the list.

## Disabling Caching

By default, all responses are cached with the TTL configured in the [`cache`][aiocache.base.BaseCache] object. To manually disable caching for responses matching a rule, set the `ttl` to 0.

!!! example
    Here is an example rule configuration that disables caching for the `/health` endpoint and enables caching for all other endpoints.

    ```python
    rules = [
        Rule("/health", ttl=0),  # Disable caching for health check
        Rule(),  # Restore default caching for other paths
    ]
    ```

## Rule Matching

### Path Rules

Path rules are used to match requests and responses based on the request path. They can be provided as a single string or a compiled regular expression. It can also be provided as a list.

!!! note
    The path rule is matched against the request path, which does not include the query string.

### Status Codes

To match on a response status codes can be provided as a single integer or as a collection of integers, like a tuple or frozenset. They can be used without a path rule to match all responses with the specified status code.

!!! example
    Here is an example rule configuration that changes the TTL based on the status code, using the default values from [Cloudflare Edge](https://developers.cloudflare.com/cache/how-to/configure-cache-status-code/#edge-ttl).

    ```python
    rules = [
        Rule(status=(200, 206, 301), ttl=60*120),   # 120m
        Rule(status=(302, 303), ttl=60*20),         # 20m
        Rule(status=(404, 410), ttl=60*3),          # 3m
    ]
    ```
