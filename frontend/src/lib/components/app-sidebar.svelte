<script lang="ts">
    import Calendars from "./calendars.svelte";
    import DatePicker from "./date-picker.svelte";
    import NavUser from "./nav-user.svelte";
    import * as Sidebar from "$lib/components/ui/sidebar/index.js";
    import type { ComponentProps } from "svelte";
    import { auth } from "$lib/state/auth.svelte";

    let {
        ref = $bindable(null),
        ...restProps
    }: ComponentProps<typeof Sidebar.Root> = $props();
</script>

<Sidebar.Root bind:ref {...restProps}>
    <Sidebar.Header class="border-sidebar-border h-16 border-b">
        <NavUser
            user={{
                name: auth.user?.name ?? "",
                email: auth.user?.email ?? "",
                avatar: auth.avatarUrl ?? "",
            }}
        />
    </Sidebar.Header>
    <Sidebar.Content>
        <DatePicker />
        <Sidebar.Separator class="mx-0" />
        <Calendars />
    </Sidebar.Content>
    <Sidebar.Footer />
    <Sidebar.Rail />
</Sidebar.Root>
