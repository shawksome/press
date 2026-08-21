# Hilay TV PressTV Rumble Feed

Automatically discovers the current HLS feed for:

https://rumble.com/v7edga2-presstv-live.html

and publishes an IPTV-compatible `presstv.m3u8`.

## Architecture

Rumble page -> GitHub Actions extractor -> `presstv.m3u8` -> Hilay TV -> OTT player

The workflow runs every 5 minutes and can also be run manually.

> Rumble HLS URLs can be temporary. GitHub Actions scheduled workflows have a minimum 5-minute interval, so if Rumble expires a URL faster than that, use the live PHP resolver on Hilay TV instead.

## Files

- `scripts/fetch_presstv.py` — discovers the Rumble embed ID and current HLS URL.
- `presstv.m3u8` — generated IPTV playlist.
- `.github/workflows/update.yml` — scheduled/manual updater.

## Hilay TV

After the repository is created, the raw playlist URL is:

`https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/hilaytv-presstv-rumble/main/presstv.m3u8`




