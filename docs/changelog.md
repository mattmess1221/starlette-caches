<style>
.md-sidebar--secondary .md-nav__list .md-nav__list {
    /* display: none */
}
</style>
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## Unreleased

### Breaking Changes

- Switch to [aiocache](https://pypi.org/project/aiocache) for caching backends. This enables you to choose between memory, redis, or memcached as backends, as well as customize how the cached data is serialized. (#1)

### New Features

- Add `match_paths` and `deny_paths` options for CacheMiddleware to allow for more fine-grained control over which paths are cached. (#8)

### Internal

- Switch build backend to hatchling.
- Run tests using github actions, with a tox config for running locally.

## Older releases

Older changes can be found in the original project's [changelog](https://github.com/florimondmanca/asgi-caches/blob/master/CHANGELOG.md).