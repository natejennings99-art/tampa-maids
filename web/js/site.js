/* Runs on every marketing page: mobile nav + config hydration. */
initHeader();
getConfig().then(hydrateBiz).catch(() => {});
