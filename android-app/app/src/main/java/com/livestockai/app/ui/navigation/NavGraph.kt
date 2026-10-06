package com.livestockai.app.ui.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.*
import androidx.navigation.navArgument
import com.livestockai.app.data.local.TokenManager
import com.livestockai.app.data.repository.*
import com.livestockai.app.ui.components.LivestockBottomNavBar
import com.livestockai.app.ui.screens.ai.*
import com.livestockai.app.ui.screens.auth.*
import com.livestockai.app.ui.screens.home.*
import com.livestockai.app.ui.screens.map.NearbyMapScreen
import com.livestockai.app.ui.screens.marketplace.*
import com.livestockai.app.ui.screens.orders.OrdersScreen
import com.livestockai.app.ui.screens.profile.ProfileScreen
import com.livestockai.app.ui.screens.scanner.*
import com.livestockai.app.ui.screens.sell.*
import com.livestockai.app.ui.screens.wishlist.WishlistScreen

@Composable
fun LivestockNavGraph(
    navController: NavHostController,
    tokenManager: TokenManager,
    authRepository: AuthRepository,
    marketplaceRepository: MarketplaceRepository,
    aiRepository: AIRepository,
    orderRepository: OrderRepository,
    modifier: Modifier = Modifier
) {
    val isLoggedIn by tokenManager.isLoggedIn.collectAsState()
    val startDestination = if (isLoggedIn) Screen.Main.route else Screen.Login.route

    NavHost(
        navController = navController,
        startDestination = startDestination,
        modifier = modifier
    ) {
        // Auth Routes
        composable(Screen.Login.route) {
            val authViewModel = remember { AuthViewModel(authRepository) }
            LoginScreen(
                viewModel = authViewModel,
                onLoginSuccess = {
                    navController.navigate(Screen.Main.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                },
                onNavigateToRegister = {
                    navController.navigate(Screen.Register.route)
                }
            )
        }

        composable(Screen.Register.route) {
            val authViewModel = remember { AuthViewModel(authRepository) }
            RegisterScreen(
                viewModel = authViewModel,
                onRegisterSuccess = {
                    navController.navigate(Screen.Main.route) {
                        popUpTo(Screen.Register.route) { inclusive = true }
                    }
                },
                onNavigateToLogin = {
                    navController.popBackStack()
                }
            )
        }

        // Main App with Bottom Navigation Bar
        composable(Screen.Main.route) {
            MainContainerScreen(
                navController = navController,
                tokenManager = tokenManager,
                authRepository = authRepository,
                marketplaceRepository = marketplaceRepository,
                aiRepository = aiRepository,
                orderRepository = orderRepository
            )
        }

        // Animal Detail
        composable(
            route = Screen.AnimalDetail.route,
            arguments = listOf(navArgument("animalId") { type = NavType.IntType })
        ) { backStackEntry ->
            val animalId = backStackEntry.arguments?.getInt("animalId") ?: 0
            AnimalDetailScreen(
                animalId = animalId,
                marketplaceRepository = marketplaceRepository,
                orderRepository = orderRepository,
                onNavigateBack = { navController.popBackStack() },
                onNavigateToOrders = { navController.navigate(Screen.Orders.route) }
            )
        }

        // Add Listing
        composable(Screen.AddListing.route) {
            val addViewModel = remember { AddListingViewModel(marketplaceRepository) }
            AddListingScreen(
                viewModel = addViewModel,
                onNavigateBack = { navController.popBackStack() },
                onSuccess = { navController.popBackStack() }
            )
        }

        // Orders
        composable(Screen.Orders.route) {
            OrdersScreen(
                orderRepository = orderRepository,
                onNavigateBack = { navController.popBackStack() }
            )
        }

        // Wishlist
        composable(Screen.Wishlist.route) {
            WishlistScreen(
                marketplaceRepository = marketplaceRepository,
                onAnimalClick = { id -> navController.navigate(Screen.AnimalDetail.createRoute(id)) },
                onNavigateBack = { navController.popBackStack() }
            )
        }

        // Nearby Mandis Map
        composable(Screen.NearbyMap.route) {
            NearbyMapScreen(
                marketplaceRepository = marketplaceRepository,
                onAnimalClick = { id -> navController.navigate(Screen.AnimalDetail.createRoute(id)) },
                onNavigateBack = { navController.popBackStack() }
            )
        }
    }
}

@Composable
fun MainContainerScreen(
    navController: NavHostController,
    tokenManager: TokenManager,
    authRepository: AuthRepository,
    marketplaceRepository: MarketplaceRepository,
    aiRepository: AIRepository,
    orderRepository: OrderRepository
) {
    val bottomNavController = rememberNavController()
    val navBackStackEntry by bottomNavController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    val bottomNavItems = listOf(
        BottomNavItem.Home,
        BottomNavItem.Marketplace,
        BottomNavItem.Scanner,
        BottomNavItem.AIChat,
        BottomNavItem.Profile
    )

    Scaffold(
        bottomBar = {
            LivestockBottomNavBar(
                items = bottomNavItems,
                currentRoute = currentRoute,
                onItemClick = { item ->
                    bottomNavController.navigate(item.route) {
                        popUpTo(bottomNavController.graph.startDestinationId) { saveState = true }
                        launchSingleTop = true
                        restoreState = true
                    }
                }
            )
        }
    ) { padding ->
        NavHost(
            navController = bottomNavController,
            startDestination = BottomNavItem.Home.route,
            modifier = Modifier.padding(padding)
        ) {
            composable(BottomNavItem.Home.route) {
                val homeViewModel = remember { HomeViewModel(marketplaceRepository) }
                HomeScreen(
                    viewModel = homeViewModel,
                    onNavigateToMarketplace = {
                        bottomNavController.navigate(BottomNavItem.Marketplace.route)
                    },
                    onAnimalClick = { id ->
                        navController.navigate(Screen.AnimalDetail.createRoute(id))
                    },
                    onNavigateToScanner = {
                        bottomNavController.navigate(BottomNavItem.Scanner.route)
                    },
                    onNavigateToAIChat = {
                        bottomNavController.navigate(BottomNavItem.AIChat.route)
                    },
                    onNavigateToNearbyMap = {
                        navController.navigate(Screen.NearbyMap.route)
                    }
                )
            }

            composable(BottomNavItem.Marketplace.route) {
                val marketViewModel = remember { MarketplaceViewModel(marketplaceRepository) }
                MarketplaceScreen(
                    viewModel = marketViewModel,
                    onAnimalClick = { id ->
                        navController.navigate(Screen.AnimalDetail.createRoute(id))
                    },
                    onAddListingClick = {
                        navController.navigate(Screen.AddListing.route)
                    }
                )
            }

            composable(BottomNavItem.Scanner.route) {
                val scannerViewModel = remember { DiseaseScannerViewModel(aiRepository) }
                DiseaseScannerScreen(
                    viewModel = scannerViewModel,
                    onNavigateToAIChat = {
                        bottomNavController.navigate(BottomNavItem.AIChat.route)
                    }
                )
            }

            composable(BottomNavItem.AIChat.route) {
                val aiViewModel = remember { AIChatViewModel(aiRepository) }
                AIChatScreen(viewModel = aiViewModel)
            }

            composable(BottomNavItem.Profile.route) {
                ProfileScreen(
                    authRepository = authRepository,
                    onNavigateToWishlist = { navController.navigate(Screen.Wishlist.route) },
                    onNavigateToOrders = { navController.navigate(Screen.Orders.route) },
                    onNavigateToNearbyMap = { navController.navigate(Screen.NearbyMap.route) },
                    onLogout = {
                        navController.navigate(Screen.Login.route) {
                            popUpTo(Screen.Main.route) { inclusive = true }
                        }
                    }
                )
            }
        }
    }
}
