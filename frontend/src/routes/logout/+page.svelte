<script lang="ts">
    import { Button } from "$lib/components/ui/button/index.js";
    import * as Card from "$lib/components/ui/card/index.js";
    import { auth } from "$lib/state/auth.svelte";

    function handleLogout() {
        auth.logout();
    }
</script>

<div class="flex h-screen w-full items-center justify-center px-4">
    <Card.Root class="mx-auto w-full max-w-sm">
        <Card.Header>
            <Card.Title class="text-2xl">Log out</Card.Title>
            <Card.Description>
                Are you sure you want to log out?
            </Card.Description>
        </Card.Header>
        <Card.Content class="flex flex-col gap-4">
            <Button class="w-full" onclick={handleLogout}>Log out</Button>
            <Button variant="outline" class="w-full" href="/">Cancel</Button>
        </Card.Content>
    </Card.Root>
</div>
