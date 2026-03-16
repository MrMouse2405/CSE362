<script lang="ts">
    import { Button } from "$lib/components/ui/button/index.js";
    import * as Card from "$lib/components/ui/card/index.js";
    import * as Avatar from "$lib/components/ui/avatar/index.js";
    import { Separator } from "$lib/components/ui/separator/index.js";
    import { auth } from "$lib/state/auth.svelte";
    import {
        SunIcon,
        MoonIcon,
        MonitorIcon,
        ShieldUser,
        User,
    } from "@lucide/svelte";
    import { resetMode, setMode, userPrefersMode } from "mode-watcher";
</script>

<div class="flex flex-1 flex-col gap-6 p-6">
    <div>
        <h1 class="text-2xl font-semibold tracking-tight">Account</h1>
        <p class="text-muted-foreground text-sm">
            Manage your profile and preferences.
        </p>
    </div>

    <Separator />

    <!-- Profile -->
    <Card.Root>
        <Card.Header>
            <Card.Title>Profile</Card.Title>
            <Card.Description>Your account information.</Card.Description>
        </Card.Header>
        <Card.Content>
            <div class="flex items-center gap-6">
                <Avatar.Root class="size-20 rounded-xl">
                    <Avatar.Image
                        src={auth.avatarUrl ?? ""}
                        alt={auth.user?.name ?? "User"}
                    />
                    <Avatar.Fallback class="rounded-xl text-2xl">
                        {(auth.user?.name ?? auth.user?.email ?? "?")
                            .charAt(0)
                            .toUpperCase()}
                    </Avatar.Fallback>
                </Avatar.Root>
                <div class="grid gap-1">
                    <p class="text-lg font-medium">
                        {auth.user?.name || "No name set"}
                    </p>
                    <p class="text-muted-foreground text-sm">
                        {auth.user?.email}
                    </p>
                    <p
                        class="text-muted-foreground flex items-center gap-1 text-xs capitalize"
                    >
                        {#if auth.user?.role === "admin"}
                            <ShieldUser class="size-3.5" />
                        {:else}
                            <User class="size-3.5" />
                        {/if}
                        {auth.user?.role}
                    </p>
                </div>
            </div>
        </Card.Content>
    </Card.Root>

    <!-- Theme -->
    <Card.Root>
        <Card.Header>
            <Card.Title>Appearance</Card.Title>
            <Card.Description>Choose your preferred theme.</Card.Description>
        </Card.Header>
        <Card.Content>
            <div class="flex gap-2">
                <Button
                    variant={userPrefersMode.current === "light"
                        ? "default"
                        : "outline"}
                    size="sm"
                    onclick={() => setMode("light")}
                >
                    <SunIcon class="mr-2 size-4" />
                    Light
                </Button>
                <Button
                    variant={userPrefersMode.current === "dark"
                        ? "default"
                        : "outline"}
                    size="sm"
                    onclick={() => setMode("dark")}
                >
                    <MoonIcon class="mr-2 size-4" />
                    Dark
                </Button>
                <Button
                    variant={userPrefersMode.current === "system"
                        ? "default"
                        : "outline"}
                    size="sm"
                    onclick={() => resetMode()}
                >
                    <MonitorIcon class="mr-2 size-4" />
                    System
                </Button>
            </div>
        </Card.Content>
    </Card.Root>
</div>
