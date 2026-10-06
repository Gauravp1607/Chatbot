package com.livestockai.app.ui.screens.map

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.NearMe
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.livestockai.app.data.repository.MarketplaceRepository
import com.livestockai.app.domain.model.Animal
import com.livestockai.app.ui.components.AnimalCard
import com.livestockai.app.ui.theme.PrimaryGreen
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NearbyMapScreen(
    marketplaceRepository: MarketplaceRepository,
    onAnimalClick: (Int) -> Unit,
    onNavigateBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    var radiusKm by remember { mutableStateOf(50f) }
    var nearbyAnimals by remember { mutableStateOf<List<Animal>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }
    val scope = rememberCoroutineScope()

    // Default Pune / Maharashtra coordinates (can be linked to Android GPS FusedLocationProviderClient)
    val userLat = 18.5204
    val userLng = 73.8567

    fun fetchNearby(radius: Double) {
        isLoading = true
        scope.launch {
            val result = marketplaceRepository.getNearbyAnimals(userLat, userLng, radius)
            nearbyAnimals = result.getOrDefault(emptyList())
            isLoading = false
        }
    }

    LaunchedEffect(Unit) {
        fetchNearby(radiusKm.toDouble())
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Nearby Livestock & Mandis", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Geolocation Header Banner
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                shape = RoundedCornerShape(16.dp),
                color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Filled.NearMe,
                            contentDescription = "GPS",
                            tint = PrimaryGreen
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Current Mandi Radius: ${radiusKm.toInt()} km",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    Slider(
                        value = radiusKm,
                        onValueChange = { radiusKm = it },
                        valueRange = 10f..200f,
                        steps = 18,
                        onValueChangeFinished = {
                            fetchNearby(radiusKm.toDouble())
                        },
                        colors = SliderDefaults.colors(thumbColor = PrimaryGreen, activeTrackColor = PrimaryGreen)
                    )

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("10 km", style = MaterialTheme.typography.labelSmall)
                        Text("200 km", style = MaterialTheme.typography.labelSmall)
                    }
                }
            }

            if (isLoading) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(color = PrimaryGreen)
                }
            } else if (nearbyAnimals.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            text = "No livestock found in ${radiusKm.toInt()} km radius",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = "Try increasing the search radius slider above.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.padding(top = 4.dp)
                        )
                    }
                }
            } else {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 16.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp),
                    contentPadding = PaddingValues(bottom = 20.dp)
                ) {
                    items(nearbyAnimals, key = { it.animalId }) { animal ->
                        AnimalCard(
                            animal = animal,
                            onClick = { onAnimalClick(animal.animalId) },
                            onFavoriteClick = {
                                scope.launch { marketplaceRepository.toggleWishlist(animal.animalId) }
                            }
                        )
                    }
                }
            }
        }
    }
}
