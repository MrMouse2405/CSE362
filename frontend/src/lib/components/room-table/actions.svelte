<script lang="ts">
    import EllipsisIcon from "@lucide/svelte/icons/ellipsis";
    import { Button } from "$lib/components/ui/button/index.js";
    import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
    import { goto } from "$app/navigation";
    import { dashboard } from "$lib/state/dashboard.svelte";

    let { roomId, roomName }: { roomId: number; roomName: string } = $props();
</script>

<DropdownMenu.Root>
    <DropdownMenu.Trigger>
        {#snippet child({ props })}
            <Button
                {...props}
                variant="ghost"
                size="icon"
                class="relative size-8 p-0"
            >
                <span class="sr-only">Open menu</span>
                <EllipsisIcon />
            </Button>
        {/snippet}
    </DropdownMenu.Trigger>
    <DropdownMenu.Content align="end">
        <DropdownMenu.Group>
            <DropdownMenu.Label>{roomName}</DropdownMenu.Label>
        </DropdownMenu.Group>
        <DropdownMenu.Separator />
        <DropdownMenu.Item
            onclick={() => goto(`/book/${roomId}/${dashboard.selectedDate}`)}
        >
            Book this room
        </DropdownMenu.Item>
    </DropdownMenu.Content>
</DropdownMenu.Root>
