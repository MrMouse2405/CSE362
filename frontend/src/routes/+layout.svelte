<script lang="ts">
    import "./layout.css";
    import { ModeWatcher } from "mode-watcher";
    import { onMount } from "svelte";
    import { Toaster, toast } from "svelte-sonner";
    import { apiFetch } from "$lib/api";
    import { goto, beforeNavigate } from "$app/navigation";
    import { page } from "$app/state";
    import { auth } from "$lib/state/auth.svelte";
    import NavUser from "$lib/components/nav-user.svelte";
    import NavUserHeader from "$lib/components/nav-user-header.svelte";
    import DatePicker from "$lib/components/date-picker.svelte";
    import Calendars from "$lib/components/calendars.svelte";

    import {
        PanelLeftIcon,
        BadgeCheckIcon,
        ShieldUser,
        CalendarCheck,
        BellIcon,
        LogOutIcon,
        LayoutDashboardIcon,
    } from "@lucide/svelte";
    import * as Sidebar from "$lib/components/ui/sidebar/index.js";
    import * as Sheet from "$lib/components/ui/sheet/index.js";
    import * as Avatar from "$lib/components/ui/avatar/index.js";
    import { Button } from "$lib/components/ui/button/index.js";
    import { Separator } from "$lib/components/ui/separator/index.js";
    import * as Breadcrumb from "$lib/components/ui/breadcrumb/index.js";
    let { children } = $props();

    let mobileNavOpen = $state(false);

    function mobileNav(path: string) {
        mobileNavOpen = false;
        goto(path);
    }

    const PAGE_NAMES: Record<string, string> = {
        "/": "Dashboard",
        "/portal": "Booking Portal",
        "/account": "Account",
        "/bookings": "Bookings",
        "/notifications": "Notifications",
        "/admin": "Admin Panel",
        "/test": "Test",
    };

    // Notification polling state
    let displayedNotifications = new Set<number>();

    onMount(() => {
        const interval = setInterval(async () => {
            if (!auth.isAuthenticated || auth.isLoading) return;

            try {
                const recent = await apiFetch<any[]>(
                    "/api/notifications/recent",
                );
                for (const n of recent) {
                    if (!displayedNotifications.has(n.id)) {
                        toast(n.message, {
                            description: new Date(n.createdAt).toLocaleString(),
                            action: {
                                label: "View",
                                onClick: () => goto("/notifications"),
                            },
                        });
                        displayedNotifications.add(n.id);
                    }
                }
            } catch (err) {
                // Silently ignore polling errors
            }
        }, 5000);

        return () => clearInterval(interval);
    });

    function pageName(pathname: string): string {
        if (pathname.startsWith("/book/")) return "Book Room";
        if (pathname.startsWith("/bookingdetails/")) return "Booking Details";
        return PAGE_NAMES[pathname] ?? pathname.split("/").pop() ?? "";
    }

    // Pages that don't require authentication
    const PUBLIC_PATHS = ["/login", "/register", "/logout"];
    // Pages that authenticated users should be redirected away from
    const GUEST_ONLY_PATHS = ["/login", "/register"];

    function isPublicPath(pathname: string): boolean {
        return PUBLIC_PATHS.some((p) => pathname.startsWith(p));
    }

    function isGuestOnlyPath(pathname: string): boolean {
        return GUEST_ONLY_PATHS.some((p) => pathname.startsWith(p));
    }

    // Guard: intercept client-side navigations to protected routes
    beforeNavigate(({ to, cancel }) => {
        const targetPath = to?.url.pathname ?? "/";

        if (
            !isPublicPath(targetPath) &&
            !auth.isLoading &&
            !auth.isAuthenticated
        ) {
            cancel();
            goto("/login");
        }
    });

    // Guard: handle direct URL visits, page reloads, and reactive auth changes.
    $effect(() => {
        if (auth.isLoading) return;

        const currentPath = page.url.pathname;

        if (!isPublicPath(currentPath) && !auth.isAuthenticated) {
            goto("/login");
        } else if (isGuestOnlyPath(currentPath) && auth.isAuthenticated) {
            goto("/");
        }

        if (currentPath.startsWith("/admin") && !auth.isAdmin) {
            goto("/portal");
        }
    });
</script>

<ModeWatcher />
<Toaster position="top-right" closeButton richColors />
<svelte:head></svelte:head>

{#if auth.isLoading}
    <div class="flex h-screen items-center justify-center">
        <p class="text-muted-foreground text-sm">Loading…</p>
    </div>
{:else if isPublicPath(page.url.pathname)}
    {@render children()}
{:else if page.url.pathname === "/"}
    <!-- Dashboard: full sidebar layout -->
    <Sidebar.Provider>
        <Sidebar.Root>
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
        <Sidebar.Inset>
            <header
                class="bg-background sticky top-0 flex h-16 shrink-0 items-center gap-2 border-b px-4"
            >
                <Sidebar.Trigger class="-ms-1" />
                <Separator
                    orientation="vertical"
                    class="me-2 data-[orientation=vertical]:h-4"
                />
                <Breadcrumb.Root>
                    <Breadcrumb.List>
                        <Breadcrumb.Item>
                            <Breadcrumb.Page>Dashboard</Breadcrumb.Page>
                        </Breadcrumb.Item>
                    </Breadcrumb.List>
                </Breadcrumb.Root>
            </header>
            <div class="flex flex-1 flex-col">
                {@render children()}
            </div>
        </Sidebar.Inset>
    </Sidebar.Provider>
{:else}
    <!-- Other authenticated pages: no sidebar, full width -->

    <!-- Mobile nav sheet -->
    <Sheet.Root bind:open={mobileNavOpen}>
        <Sheet.Content side="left" class="w-72 p-0">
            <Sheet.Header class="sr-only">
                <Sheet.Title>Navigation</Sheet.Title>
                <Sheet.Description>App navigation menu</Sheet.Description>
            </Sheet.Header>
            <div class="border-b p-4">
                <div class="flex items-center gap-3">
                    <Avatar.Root class="size-9 rounded-lg">
                        <Avatar.Image
                            src={auth.avatarUrl ?? ""}
                            alt={auth.user?.name ?? "User"}
                        />
                        <Avatar.Fallback class="rounded-lg">CN</Avatar.Fallback>
                    </Avatar.Root>
                    <div class="grid text-sm leading-tight">
                        <span class="truncate font-medium"
                            >{auth.user?.name || auth.user?.email}</span
                        >
                        <span class="text-muted-foreground truncate text-xs"
                            >{auth.user?.email}</span
                        >
                    </div>
                </div>
            </div>
            <nav class="flex flex-col gap-1 p-2">
                {#if auth.isSuperuser}
                    <Button
                        variant="ghost"
                        class="justify-start gap-2"
                        onclick={() => mobileNav("/admin")}
                    >
                        <ShieldUser class="size-4" />
                        Admin Panel
                    </Button>
                    <Separator class="my-1" />
                {/if}
                <Button
                    variant="ghost"
                    class="justify-start gap-2"
                    onclick={() => mobileNav("/portal")}
                >
                    <CalendarCheck class="size-4" />
                    Booking Portal
                </Button>
                <Button
                    variant="ghost"
                    class="justify-start gap-2"
                    onclick={() => mobileNav("/")}
                >
                    <LayoutDashboardIcon class="size-4" />
                    Dashboard
                </Button>
                <Button
                    variant="ghost"
                    class="justify-start gap-2"
                    onclick={() => mobileNav("/account")}
                >
                    <BadgeCheckIcon class="size-4" />
                    Account
                </Button>
                <Button
                    variant="ghost"
                    class="justify-start gap-2"
                    onclick={() => mobileNav("/bookings")}
                >
                    <CalendarCheck class="size-4" />
                    Bookings
                </Button>
                <Button
                    variant="ghost"
                    class="justify-start gap-2"
                    onclick={() => mobileNav("/notifications")}
                >
                    <BellIcon class="size-4" />
                    Notifications
                </Button>
                <Separator class="my-1" />
                <Button
                    variant="ghost"
                    class="justify-start gap-2 text-red-500 hover:text-red-600"
                    onclick={() => mobileNav("/logout")}
                >
                    <LogOutIcon class="size-4" />
                    Log out
                </Button>
            </nav>
        </Sheet.Content>
    </Sheet.Root>

    <div class="flex min-h-screen flex-col">
        <header
            class="bg-background sticky top-0 flex h-16 shrink-0 items-center gap-2 border-b px-4"
        >
            <!-- Mobile: hamburger menu -->
            <Button
                variant="ghost"
                size="icon"
                class="md:hidden"
                onclick={() => (mobileNavOpen = true)}
            >
                <PanelLeftIcon class="size-5" />
                <span class="sr-only">Toggle navigation</span>
            </Button>
            <!-- Desktop: user dropdown -->
            <div class="hidden md:block">
                <NavUserHeader
                    user={{
                        name: auth.user?.name ?? "",
                        email: auth.user?.email ?? "",
                        avatar: auth.avatarUrl ?? "",
                    }}
                />
            </div>
            <Separator
                orientation="vertical"
                class="mx-2 data-[orientation=vertical]:h-4"
            />
            <Breadcrumb.Root>
                <Breadcrumb.List>
                    <Breadcrumb.Item class="hidden md:block">
                        <Breadcrumb.Link href="/">Dashboard</Breadcrumb.Link>
                    </Breadcrumb.Item>
                    <Breadcrumb.Separator class="hidden md:block" />
                    <Breadcrumb.Item>
                        <Breadcrumb.Page
                            >{pageName(page.url.pathname)}</Breadcrumb.Page
                        >
                    </Breadcrumb.Item>
                </Breadcrumb.List>
            </Breadcrumb.Root>
        </header>
        <div class="flex flex-1 flex-col">
            {@render children()}
        </div>
    </div>
{/if}
