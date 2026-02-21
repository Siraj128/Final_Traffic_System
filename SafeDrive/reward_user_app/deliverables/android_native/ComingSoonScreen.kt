package com.safedrive.rewards.ui.screens

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Construction
import androidx.compose.material.icons.rounded.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController

// 🎨 COLOR THEME
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
}

@Composable
fun MainScreen() {
    val navController = rememberNavController()
    
    Scaffold(
        bottomBar = { BottomNavBar(navController) },
        floatingActionButton = { ScanFAB(onClick = { navController.navigate("scan") }) },
        floatingActionButtonPosition = FabPosition.Center,
        containerColor = AppTheme.BackgroundLight
    ) { innerPadding ->
        Box(modifier = Modifier.padding(innerPadding)) {
            NavigationGraph(navController)
        }
    }
}

@Composable
fun NavigationGraph(navController: NavController) {
    // 🧭 NAVIGATION LOGIC
    // Home -> Dashboard (Placeholder)
    // Rewards -> Coming Soon
    // Scan -> FASTag Scanner (Placeholder)
    // Alerts -> Coming Soon
    // Profile -> Coming Soon
    
    NavHost(navController = navController as androidx.navigation.NavHostController, startDestination = "home") {
        composable("home") { DashboardPlaceholder() }
        composable("rewards") { ComingSoonScreen() }
        composable("scan") { FastTagScannerPlaceholder() }
        composable("alerts") { ComingSoonScreen() }
        composable("profile") { ComingSoonScreen() }
    }
}

@Composable
fun ComingSoonScreen() {
    // 📱 SCREEN TYPE: "Coming Soon / Under Development" placeholder
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(AppTheme.BackgroundLight),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // 2️⃣ CENTER ICON
        Icon(
            imageVector = Icons.Default.Construction,
            contentDescription = "Under Development",
            tint = AppTheme.ConstructionIconColor,
            modifier = Modifier.size(120.dp)
        )

        Spacer(modifier = Modifier.height(16.dp))

        // 3️⃣ TITLE TEXT
        Text(
            text = "Coming Soon",
            fontSize = 20.sp,
            fontWeight = FontWeight.Medium,
            color = AppTheme.TextSecondary,
            // fontFamily = FontFamily.Poppins (Assuming loaded)
        )

        Spacer(modifier = Modifier.height(8.dp))

        // 4️⃣ OPTIONAL SUBTEXT
        Text(
            text = "This feature is under development",
            fontSize = 14.sp,
            color = AppTheme.TextTertiary
        )
    }
}

@Composable
fun BottomNavBar(navController: NavController) {
    // 🔻 BOTTOM NAVIGATION BAR
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
            val currentRoute = navController.currentBackStackEntryAsState().value?.destination?.route

            // Left Items
            NavBarItem(
                icon = Icons.Rounded.Home,
                label = "Home",
                selected = currentRoute == "home",
                onClick = { navController.navigate("home") }
            )
            NavBarItem(
                icon = Icons.Rounded.Star,
                label = "Rewards",
                selected = currentRoute == "rewards",
                onClick = { navController.navigate("rewards") }
            )

            // Spacing for FAB
            Spacer(modifier = Modifier.weight(1f)) 

            // Right Items
            NavBarItem(
                icon = Icons.Rounded.Notifications, // Warning/Bell
                label = "Alerts",
                selected = currentRoute == "alerts",
                onClick = { navController.navigate("alerts") }
            )
            NavBarItem(
                icon = Icons.Rounded.Person,
                label = "Profile",
                selected = currentRoute == "profile",
                onClick = { navController.navigate("profile") }
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
        onClick = onClick,
        colors = NavigationBarItemDefaults.colors(
            indicatorColor = Color.Transparent
        )
    )
}

@Composable
fun ScanFAB(onClick: () -> Unit) {
    // 🔵 CENTER SCAN FAB BUTTON
    
    // FAB Animation (Pulse effect placeholder)
    val infiniteTransition = rememberInfiniteTransition()
    val glowRadio by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 10f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        )
    )

    Box(
        modifier = Modifier
            .offset(y = (-30).dp) // Floating above navbar
            .size(80.dp) // Includes glow space
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

// Placeholders for context
@Composable
fun DashboardPlaceholder() { Box(Modifier.fillMaxSize()) { Text("Dashboard", Modifier.align(Alignment.Center)) } }
@Composable
fun FastTagScannerPlaceholder() { Box(Modifier.fillMaxSize()) { Text("Scanner", Modifier.align(Alignment.Center)) } }
