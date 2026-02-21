package com.example.reward_user_app

import android.app.Activity
import android.widget.Toast
import androidx.activity.compose.BackHandler
import androidx.compose.animation.*
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Construction
import androidx.compose.material.icons.rounded.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController

// 🎨 COLOR THEME (Reused & Expanded)
object AppTheme {
    val PrimaryGradient = Brush.linearGradient(
        colors = listOf(Color(0xFF1E2D4C), Color(0xFF30B7FF))
    )
    val NavBarGradient = Brush.verticalGradient(
        colors = listOf(Color(0xFF0F172A), Color(0xFF1E293B))
    )
    val ScanFabGradient = Brush.linearGradient(
        colors = listOf(Color(0xFF30B7FF), Color(0xFF6A7BFF))
    )
    val BackgroundLight = Color(0xFFF5F7FA)
    val BackgroundDark = Color(0xFF0F172A)
    val TextPrimary = Color(0xFF1E2D4C)
    val TextSecondary = Color(0xFF858585)
    val TextTertiary = Color(0xFFA0A7B5)
    val ConstructionIconColor = Color(0xFFC0C7D1)
    val Accent = Color(0xFF30B7FF)
    val White = Color.White
    val DarkHeaderIconColor = Color.White
    val LightHeaderIconColor = Color(0xFF1E2D4C)
}

// 🧭 ROUTES
object Routes {
    const val HOME = "home"
    const val REWARDS = "rewards"
    const val SCAN = "scan"
    const val ALERTS = "alerts"
    const val PROFILE = "profile"
    
    // Detail Screens
    const val LEADERBOARD = "leaderboard"
    const val REWARD_CARD = "reward_card"
    const val FASTAG_PAYMENT = "fastag_payment"
    const val DRIVING_ANALYTICS = "driving_analytics"
    const val NOTIFICATIONS_DETAILS = "notifications_details"
    const val REDEMPTION_CATALOG = "redemption_catalog"
    const val PROFILE_EDIT = "profile_edit"
    const val VEHICLE_DETAILS = "vehicle_details"
    const val TRANSACTION_HISTORY = "transaction_history"
    const val SETTINGS = "settings"
}

@Composable
fun SafeDriveApp() {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    // Define Root Screens (No Back Button, Yes Bottom Bar)
    val rootScreens = listOf(Routes.HOME, Routes.REWARDS, Routes.SCAN, Routes.ALERTS, Routes.PROFILE)
    val isRootScreen = currentRoute in rootScreens

    Scaffold(
        topBar = {
            // Only show TopBar if NOT on Home (Home usually has custom header) or specific design requiring it.
            // Requirement says: "Add a back arrow icon on the top-left of all inner screens."
            // "DO NOT add back button on: Home, Rewards main tab, Alerts main tab, Profile main tab, Scan tab"
            if (!isRootScreen) {
                CustomTopAppBar(
                    title = getTitleForRoute(currentRoute),
                    onBackClick = { navController.popBackStack() },
                    isLight = isRouteLight(currentRoute)
                )
            }
        },
        bottomBar = {
            if (isRootScreen) {
                BottomNavBar(navController, currentRoute)
            }
        },
        floatingActionButton = {
            if (isRootScreen) {
                ScanFAB(onClick = { navController.navigate(Routes.SCAN) })
            }
        },
        floatingActionButtonPosition = FabPosition.Center,
        containerColor = AppTheme.BackgroundLight
    ) { innerPadding ->
        // Handle Home Screen Exit Logic
        if (currentRoute == Routes.HOME) {
            val context = LocalContext.current
            var backPressedTime by remember { mutableLongStateOf(0L) }
            BackHandler(enabled = true) {
                val currentTime = System.currentTimeMillis()
                if (currentTime - backPressedTime < 2000) {
                    (context as? Activity)?.finish()
                } else {
                    backPressedTime = currentTime
                    Toast.makeText(context, "Press back again to exit", Toast.LENGTH_SHORT).show()
                }
            }
        }

        Box(modifier = Modifier.padding(innerPadding)) {
            NavigationGraph(navController)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CustomTopAppBar(title: String, onBackClick: () -> Unit, isLight: Boolean = false) {
    TopAppBar(
        title = {
            Text(
                text = title,
                color = if (isLight) AppTheme.TextPrimary else AppTheme.White,
                fontWeight = FontWeight.Bold
            )
        },
        navigationIcon = {
            IconButton(onClick = onBackClick) {
                Icon(
                    imageVector = Icons.AutoMirrored.Filled.ArrowBack, // 24dp default
                    contentDescription = "Back",
                    tint = if (isLight) AppTheme.LightHeaderIconColor else AppTheme.DarkHeaderIconColor,
                    modifier = Modifier.padding(start = 8.dp) // Total padding logic handled by IconButton default + this
                )
            }
        },
        colors = TopAppBarDefaults.topAppBarColors(
            containerColor = if (isLight) AppTheme.BackgroundLight else Color(0xFF1E2D4C) // approximates gradient start for mockup
            // For real gradient background in TopAppBar, we'd need a custom Box component, sticking to solid for standard TopAppBar for now
            // or we use a Box behind it. User asked for "White on dark header, #1E2D4C on light header".
        )
    )
}

// Helper to get titles
fun getTitleForRoute(route: String?): String {
    return when (route) {
        Routes.LEADERBOARD -> "Leaderboard"
        Routes.REWARD_CARD -> "Reward Details"
        Routes.FASTAG_PAYMENT -> "FASTag Payment"
        Routes.DRIVING_ANALYTICS -> "Driving Analytics"
        Routes.NOTIFICATIONS_DETAILS -> "Notification"
        Routes.REDEMPTION_CATALOG -> "Redemption Catalog"
        Routes.PROFILE_EDIT -> "Edit Profile"
        Routes.VEHICLE_DETAILS -> "Vehicle Details"
        Routes.TRANSACTION_HISTORY -> "Transactions"
        Routes.SETTINGS -> "Settings"
        else -> ""
    }
}

// Helper to decide if header is light (dark text/icon) or dark (white text/icon)
fun isRouteLight(route: String?): Boolean {
    // Arbitrary design choice mostly, assuming most detail screens might have white backgrounds
    // User spec: "White on dark header #1E2D4C on light header"
    // Let's assume most screens like Settings, Edit Profile are Light.
    // Leaderboard might be Dark.
    return when (route) {
        Routes.SETTINGS, Routes.PROFILE_EDIT, Routes.VEHICLE_DETAILS -> true
        else -> false // Default to Dark Header for that "premium" feel
    }
}

@Composable
fun NavigationGraph(navController: NavController) {
    NavHost(
        navController = navController as androidx.navigation.NavHostController,
        startDestination = Routes.HOME,
        enterTransition = { slideIntoContainer(AnimatedContentTransitionScope.SlideDirection.Left, animationSpec = tween(300)) },
        exitTransition = { slideOutOfContainer(AnimatedContentTransitionScope.SlideDirection.Left, animationSpec = tween(300)) }, // Push out to left
        popEnterTransition = { slideIntoContainer(AnimatedContentTransitionScope.SlideDirection.Right, animationSpec = tween(300)) }, // Slide in from left
        popExitTransition = { slideOutOfContainer(AnimatedContentTransitionScope.SlideDirection.Right, animationSpec = tween(300)) } // Slide out to right
    ) {
        // Root Tabs
        composable(Routes.HOME) { HomeScreen(navController) }
        composable(Routes.REWARDS) { PlaceholderScreen("Rewards Main", navController) }
        composable(Routes.SCAN) { ScannerScreen(navController) }
        composable(Routes.ALERTS) { PlaceholderScreen("Alerts Main", navController) }
        composable(Routes.PROFILE) { PlaceholderScreen("Profile Main", navController) }

        // Detail Screens
        composable(Routes.LEADERBOARD) { DetailScreen("Leaderboard Content") }
        composable(Routes.REWARD_CARD) { DetailScreen("Reward Card Info") }
        composable(Routes.FASTAG_PAYMENT) { PaymentScreen(navController) }
        composable(Routes.DRIVING_ANALYTICS) { DetailScreen("Analytics Graph") }
        composable(Routes.NOTIFICATIONS_DETAILS) { DetailScreen("Full Notification") }
        composable(Routes.REDEMPTION_CATALOG) { DetailScreen("Catalog Items") }
        composable(Routes.PROFILE_EDIT) { DetailScreen("Edit Profile Forms") }
        composable(Routes.VEHICLE_DETAILS) { DetailScreen("Vehicle Info") }
        composable(Routes.TRANSACTION_HISTORY) { DetailScreen("Transaction List") }
        composable(Routes.SETTINGS) { DetailScreen("Settings Options") }
    }
}

// 🏠 SCREENS
@Composable
fun HomeScreen(navController: NavController) {
    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text("Home Screen", fontSize = 24.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(20.dp))
        Button(onClick = { navController.navigate(Routes.LEADERBOARD) }) { Text("Go to Leaderboard") }
        Button(onClick = { navController.navigate(Routes.DRIVING_ANALYTICS) }) { Text("Go to Analytics") }
        Button(onClick = { navController.navigate(Routes.SETTINGS) }) { Text("Go to Settings") }
    }
}

@Composable
fun ScannerScreen(navController: NavController) {
    // Edge Case: Back -> Stop camera -> Return Home
    BackHandler {
        // Logic to stop camera would go here
        navController.popBackStack(Routes.HOME, inclusive = false)
    }
    
    Box(Modifier.fillMaxSize().background(Color.Black)) {
        Text("Camera View (Mock)", color = Color.White, modifier = Modifier.align(Alignment.Center))
        Button(
            onClick = { navController.popBackStack(Routes.HOME, inclusive = false) },
            modifier = Modifier.align(Alignment.BottomCenter).padding(32.dp)
        ) {
            Text("Stop Camera & Return Home")
        }
    }
}

@Composable
fun PaymentScreen(navController: NavController) {
    // Edge Case: Back -> Confirm cancel popup
    var showDialog by remember { mutableStateOf(false) }

    if (showDialog) {
        AlertDialog(
            onDismissRequest = { showDialog = false },
            title = { Text("Cancel Payment?") },
            text = { Text("Are you sure you want to cancel this transaction?") },
            confirmButton = {
                TextButton(onClick = { 
                    showDialog = false 
                    navController.popBackStack()
                }) { Text("Yes, Cancel") }
            },
            dismissButton = {
                TextButton(onClick = { showDialog = false }) { Text("No") }
            }
        )
    }

    BackHandler {
        showDialog = true
    }

    Column(Modifier.fillMaxSize(), verticalArrangement = Arrangement.Center, horizontalAlignment = Alignment.CenterHorizontally) {
        Text("Payment Processing...")
    }
}

@Composable
fun PlaceholderScreen(name: String, navController: NavController) {
    Column(Modifier.fillMaxSize(), verticalArrangement = Arrangement.Center, horizontalAlignment = Alignment.CenterHorizontally) {
        Text(name, fontSize = 24.sp)
        if (name == "Rewards Main") {
            Button(onClick = { navController.navigate(Routes.REWARD_CARD) }) { Text("View Reward Details") }
            Button(onClick = { navController.navigate(Routes.REDEMPTION_CATALOG) }) { Text("Redemption Catalog") }
        }
        if (name == "Profile Main") {
            Button(onClick = { navController.navigate(Routes.PROFILE_EDIT) }) { Text("Edit Profile") }
            Button(onClick = { navController.navigate(Routes.VEHICLE_DETAILS) }) { Text("Vehicle Details") }
            Button(onClick = { navController.navigate(Routes.TRANSACTION_HISTORY) }) { Text("Transactions") }
        }
    }
}

@Composable
fun DetailScreen(content: String) {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text(content, fontSize = 20.sp)
    }
}

@Composable
fun BottomNavBar(navController: NavController, currentRoute: String?) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(80.dp)
            .shadow(elevation = 16.dp, shape = RoundedCornerShape(topStart = 32.dp, topEnd = 32.dp))
            .background(brush = AppTheme.NavBarGradient, shape = RoundedCornerShape(topStart = 32.dp, topEnd = 32.dp))
    ) {
        NavigationBar(
            containerColor = Color.Transparent,
            tonalElevation = 0.dp,
            modifier = Modifier.align(Alignment.Center)
        ) {
            NavBarItem(
                icon = Icons.Rounded.Home,
                label = "Home",
                selected = currentRoute == Routes.HOME,
                onClick = { navController.navigate(Routes.HOME) }
            )
            NavBarItem(
                icon = Icons.Rounded.Star,
                label = "Rewards",
                selected = currentRoute == Routes.REWARDS,
                onClick = { navController.navigate(Routes.REWARDS) }
            )
            Spacer(modifier = Modifier.weight(1f)) 
            NavBarItem(
                icon = Icons.Rounded.Notifications,
                label = "Alerts",
                selected = currentRoute == Routes.ALERTS,
                onClick = { navController.navigate(Routes.ALERTS) }
            )
            NavBarItem(
                icon = Icons.Rounded.Person,
                label = "Profile",
                selected = currentRoute == Routes.PROFILE,
                onClick = { navController.navigate(Routes.PROFILE) }
            )
        }
    }
}

@Composable
fun RowScope.NavBarItem(icon: ImageVector, label: String, selected: Boolean, onClick: () -> Unit) {
    NavigationBarItem(
        icon = { 
            Icon(
                imageVector = icon, 
                contentDescription = label,
                tint = if (selected) AppTheme.Accent else AppTheme.TextSecondary
            ) 
        },
        label = { 
            Text(
                text = label, 
                color = if (selected) AppTheme.Accent else AppTheme.TextSecondary,
                fontSize = 10.sp
            ) 
        },
        selected = selected,
        onClick = {
            if (!selected) {
                 onClick()
            }
        },
        colors = NavigationBarItemDefaults.colors(
            indicatorColor = Color.Transparent
        )
    )
}

@Composable
fun ScanFAB(onClick: () -> Unit) {
    Box(
        modifier = Modifier
            .offset(y = (-30).dp)
            .size(80.dp)
            .shadow(elevation = 10.dp, shape = CircleShape, spotColor = AppTheme.Accent)
            .background(Color.Transparent),
        contentAlignment = Alignment.Center
    ) {
        FloatingActionButton(
            onClick = onClick,
            shape = CircleShape,
            containerColor = Color.Transparent,
            elevation = FloatingActionButtonDefaults.elevation(0.dp),
            modifier = Modifier
                .size(72.dp)
                .background(brush = AppTheme.ScanFabGradient, shape = CircleShape)
        ) {
            Icon(
                imageVector = Icons.Rounded.QrCodeScanner,
                contentDescription = "Scan",
                tint = Color.White,
                modifier = Modifier.size(32.dp)
            )
        }
    }
}
