<script lang="ts">
    import "./layout.css";
    import { ModeWatcher } from "mode-watcher";
    import { goto, beforeNavigate } from "$app/navigation";
    import { page } from "$app/state";
    import { auth } from "$lib/state/auth.svelte";
    let { children } = $props();

    const PUBLIC_PATHS = ["/login", "/register"];

    // 1. Guard against clicking links (Client-side navigation)
    beforeNavigate(({ to, cancel }) => {
        const targetPath = to?.url.pathname ?? "/";
        const isPublicPath = PUBLIC_PATHS.some((path) =>
            targetPath.startsWith(path),
        );

        if (!isPublicPath && !auth.isAuthenticated) {
            cancel(); // Stop the navigation instantly
            goto("/login");
        }
    });

    // 2. Guard against direct URL visits and react to auth changes
    $effect(() => {
        // We subscribe to the current path and auth state
        const currentPath = page.url.pathname;
        const isPublicPath = PUBLIC_PATHS.some((path) =>
            currentPath.startsWith(path),
        );

        // If a user logs out while on a private page, or loads it directly, boot them
        if (!isPublicPath && !auth.isAuthenticated) {
            goto("/login");
        }
    });
</script>

<ModeWatcher />
<svelte:head></svelte:head>
{@render children()}
