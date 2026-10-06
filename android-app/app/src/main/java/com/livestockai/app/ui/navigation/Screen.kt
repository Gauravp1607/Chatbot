package com.livestockai.app.ui.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.ui.graphics.vector.ImageVector

sealed class Screen(val route: String) {
    object Splash : Screen("splash")
    object Login : Screen("login")
    object Register : Screen("register")
    object Main : Screen("main")
    object AnimalDetail : Screen("animal_detail/{animalId}") {
        fun createRoute(animalId: Int) = "animal_detail/$animalId"
    }
    object AddListing : Screen("add_listing")
    object NearbyMap : Screen("nearby_map")
    object Wishlist : Screen("wishlist")
    object Orders : Screen("orders")
}

sealed class BottomNavItem(
    val route: String,
    val title: String,
    val selectedIcon: ImageVector,
    val unselectedIcon: ImageVector
) {
    object Home : BottomNavItem("home_tab", "Home", Icons.Filled.Home, Icons.Outlined.Home)
    object Marketplace : BottomNavItem("market_tab", "Market", Icons.Filled.Storefront, Icons.Outlined.Storefront)
    object Scanner : BottomNavItem("scanner_tab", "Vet Scanner", Icons.Filled.HealthAndSafety, Icons.Outlined.HealthAndSafety)
    object AIChat : BottomNavItem("ai_tab", "AI Vet", Icons.Filled.SmartToy, Icons.Outlined.SmartToy)
    object Profile : BottomNavItem("profile_tab", "Profile", Icons.Filled.Person, Icons.Outlined.Person)
}
