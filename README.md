# Kid Odysseus — website & web build

Astro site published on GitHub Pages at https://kuragestudios.github.io/kid-odysseus/

- `/` landing page (features, screenshots, download links)
- `/play/` the game, full window
- `/game/` the raw Unity WebGL build (copied from the Unity project by `Deploy/github-pages/publish-web.sh`)

```sh
npm install
npm run dev      # http://localhost:4321/kid-odysseus/
npm run build    # dist/
```

Deploy: push to `main`; `.github/workflows/deploy.yml` builds and publishes to Pages
(Settings > Pages > Source: GitHub Actions).
