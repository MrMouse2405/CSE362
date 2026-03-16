<script lang="ts">
    import { page } from "$app/state";
    import { Button } from "$lib/components/ui/button/index.js";
</script>

<div
    class="flex h-screen w-full flex-col items-center justify-center gap-4 px-4"
>
    <h1 class="text-6xl font-bold tracking-tight">{page.status}</h1>
    <p class="text-muted-foreground text-lg">
        {page.error?.message ?? "Page not found"}
    </p>
    <Button href="/">Go home</Button>
</div>
