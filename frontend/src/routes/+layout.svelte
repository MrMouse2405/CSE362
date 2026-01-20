<script lang="ts">
    import "./layout.css";
    import { ModeWatcher } from "mode-watcher";
    let { children } = $props();
</script>

<svelte:head>
    <title>CSE362</title>
</svelte:head>

<ModeWatcher />
{@render children()}
