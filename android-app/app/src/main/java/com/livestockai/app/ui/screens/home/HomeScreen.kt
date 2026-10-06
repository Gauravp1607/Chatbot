package com.livestockai.app.ui.screens.home

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.livestockai.app.ui.components.AnimalCard
import com.livestockai.app.ui.theme.*

@Composable
fun HomeScreen(
    viewModel: HomeViewModel,
    onNavigateToMarketplace: (String?) -> Unit,
    onAnimalClick: (Int) -> Unit,
    onNavigateToScanner: () -> Unit,
    onNavigateToAIChat: () -> Unit,
    onNavigateToNearbyMap: () -> Unit,
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            HomeTopBar(
                onMapClick = onNavigateToNearbyMap
            )
        }
    ) { padding ->
        if (uiState.isLoading) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator(color = PrimaryGreen)
            }
        } else {
            LazyColumn(
                modifier = modifier
                    .fillMaxSize()
                    .padding(padding),
                contentPadding = PaddingValues(bottom = 24.dp)
            ) {
                // 1. AI Hero Diagnostic & Marketplace Banner
                item {
                    AIHeroBanner(
                        onScanClick = onNavigateToScanner,
                        onAskAIClick = onNavigateToAIChat
                    )
                }

                // 2. Categories Section
                item {
                    SectionHeader(
                        title = "Explore Categories",
                        onSeeAll = { onNavigateToMarketplace(null) }
                    )

                    LazyRow(
                        contentPadding = PaddingValues(horizontal = 16.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        items(uiState.categories) { category ->
                            CategoryItem(
                                category = category,
                                onClick = { onNavigateToMarketplace(category) }
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(20.dp))
                }

                // 3. Featured Livestock Cards
                if (uiState.featuredAnimals.isNotEmpty()) {
                    item {
                        SectionHeader(
                            title = "Featured Animals",
                            onSeeAll = { onNavigateToMarketplace(null) }
                        )

                        LazyRow(
                            contentPadding = PaddingValues(horizontal = 16.dp),
                            horizontalArrangement = Arrangement.spacedBy(14.dp)
                        ) {
                            items(uiState.featuredAnimals) { animal ->
                                Box(modifier = Modifier.width(260.dp)) {
                                    AnimalCard(
                                        animal = animal,
                                        onClick = { onAnimalClick(animal.animalId) },
                                        onFavoriteClick = { viewModel.toggleFavorite(animal.animalId) }
                                    )
                                }
                            }
                        }

                        Spacer(modifier = Modifier.height(24.dp))
                    }
                }

                // 4. Recent Verified Listings
                item {
                    SectionHeader(
                        title = "Recent Listings",
                        onSeeAll = { onNavigateToMarketplace(null) }
                    )
                }

                items(uiState.recentAnimals) { animal ->
                    Box(modifier = Modifier.padding(horizontal = 16.dp, vertical = 6.dp)) {
                        AnimalCard(
                            animal = animal,
                            onClick = { onAnimalClick(animal.animalId) },
                            onFavoriteClick = { viewModel.toggleFavorite(animal.animalId) }
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun HomeTopBar(onMapClick: () -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp, vertical = 14.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column {
            Text(
                text = "LivestockAI",
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.ExtraBold,
                color = PrimaryGreen
            )
            Text(
                text = "Find & Care for Livestock Near You",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        IconButton(
            onClick = onMapClick,
            modifier = Modifier
                .size(44.dp)
                .background(PrimaryGreen.copy(alpha = 0.1f), CircleShape)
        ) {
            Icon(
                imageVector = Icons.Filled.LocationOn,
                contentDescription = "Nearby Animals Map",
                tint = PrimaryGreen
            )
        }
    }
}

@Composable
fun AIHeroBanner(
    onScanClick: () -> Unit,
    onAskAIClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent)
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    Brush.horizontalGradient(
                        colors = listOf(PrimaryGreenDark, PrimaryGreenLight)
                    )
                )
                .padding(20.dp)
        ) {
            Column {
                Row(
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Surface(
                        shape = CircleShape,
                        color = AmberAccent
                    ) {
                        Text(
                            text = "AI Vet Powered",
                            color = Color.Black,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(10.dp))

                Text(
                    text = "Instant Animal Health & Disease Diagnosis",
                    style = MaterialTheme.typography.titleLarge,
                    color = Color.White,
                    fontWeight = FontWeight.Bold
                )

                Text(
                    text = "Snap a photo of your cow, dog, cat or horse to detect symptoms and get instant veterinary care guidance.",
                    style = MaterialTheme.typography.bodySmall,
                    color = Color.White.copy(alpha = 0.85f),
                    modifier = Modifier.padding(top = 4.dp, bottom = 14.dp)
                )

                Row(
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Button(
                        onClick = onScanClick,
                        colors = ButtonDefaults.buttonColors(containerColor = AmberAccent),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Filled.CameraAlt,
                            contentDescription = "Scan",
                            tint = Color.Black,
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "Scan Animal",
                            color = Color.Black,
                            fontWeight = FontWeight.Bold
                        )
                    }

                    OutlinedButton(
                        onClick = onAskAIClick,
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = Color.White),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Color.White.copy(alpha = 0.6f))
                    ) {
                        Icon(
                            imageVector = Icons.Filled.SmartToy,
                            contentDescription = "Ask AI",
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(text = "Ask AI")
                    }
                }
            }
        }
    }
}

@Composable
fun SectionHeader(
    title: String,
    onSeeAll: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 10.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold
        )
        TextButton(onClick = onSeeAll) {
            Text(
                text = "See All",
                color = PrimaryGreen,
                fontWeight = FontWeight.SemiBold
            )
        }
    }
}

@Composable
fun CategoryItem(
    category: String,
    onClick: () -> Unit
) {
    Surface(
        modifier = Modifier
            .clip(RoundedCornerShape(16.dp))
            .clickable { onClick() },
        color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f),
        shape = RoundedCornerShape(16.dp)
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            val icon = when (category.lowercase()) {
                "cow" -> "🐄"
                "dog" -> "🐕"
                "cat" -> "🐈"
                "horse" -> "🐎"
                else -> "🐾"
            }
            Text(text = icon, fontSize = 20.sp)
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = category,
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.Bold
            )
        }
    }
}
