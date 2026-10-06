package com.livestockai.app.ui.screens.marketplace

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.livestockai.app.data.repository.MarketplaceRepository
import com.livestockai.app.data.repository.OrderRepository
import com.livestockai.app.domain.model.Animal
import com.livestockai.app.ui.theme.*
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AnimalDetailScreen(
    animalId: Int,
    marketplaceRepository: MarketplaceRepository,
    orderRepository: OrderRepository,
    onNavigateBack: () -> Unit,
    onNavigateToOrders: () -> Unit,
    modifier: Modifier = Modifier
) {
    var animal by remember { mutableStateOf<Animal?>(null) }
    var isLoading by remember { mutableStateOf(true) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    var isOrdering by remember { mutableStateOf(false) }

    val scope = rememberCoroutineScope()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(animalId) {
        isLoading = true
        val result = marketplaceRepository.getAnimalDetail(animalId)
        result.onSuccess {
            animal = it
            isLoading = false
        }.onFailure {
            errorMessage = it.message ?: "Failed to load animal details"
            isLoading = false
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = { Text(animal?.animalName ?: "Livestock Details", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    animal?.let { a ->
                        IconButton(onClick = {
                            scope.launch {
                                marketplaceRepository.toggleWishlist(a.animalId)
                                snackbarHostState.showSnackbar("Wishlist updated")
                            }
                        }) {
                            Icon(Icons.Filled.FavoriteBorder, contentDescription = "Favorite")
                        }
                    }
                }
            )
        },
        bottomBar = {
            animal?.let { a ->
                Surface(
                    color = MaterialTheme.colorScheme.surface,
                    tonalElevation = 8.dp,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column {
                            Text(
                                text = "Total Price",
                                style = MaterialTheme.typography.labelMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Text(
                                text = a.formattedPrice,
                                style = MaterialTheme.typography.headlineSmall,
                                fontWeight = FontWeight.ExtraBold,
                                color = PrimaryGreen
                            )
                        }

                        Button(
                            onClick = {
                                scope.launch {
                                    isOrdering = true
                                    val res = orderRepository.createOrder(a.animalId)
                                    isOrdering = false
                                    res.onSuccess {
                                        snackbarHostState.showSnackbar("Order created successfully!")
                                        onNavigateToOrders()
                                    }.onFailure { err ->
                                        snackbarHostState.showSnackbar(err.message ?: "Order creation failed")
                                    }
                                }
                            },
                            enabled = !isOrdering && a.availability == "Available",
                            shape = RoundedCornerShape(14.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = PrimaryGreen),
                            modifier = Modifier.height(50.dp)
                        ) {
                            if (isOrdering) {
                                CircularProgressIndicator(color = Color.White, modifier = Modifier.size(20.dp))
                            } else {
                                Icon(Icons.Filled.ShoppingBag, contentDescription = "Buy")
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Buy Now", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                            }
                        }
                    }
                }
            }
        }
    ) { padding ->
        if (isLoading) {
            Box(
                modifier = Modifier.fillMaxSize().padding(padding),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator(color = PrimaryGreen)
            }
        } else if (animal != null) {
            val a = animal!!
            Column(
                modifier = modifier
                    .fillMaxSize()
                    .padding(padding)
                    .verticalScroll(rememberScrollState())
            ) {
                // Main Photo
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(260.dp)
                ) {
                    AsyncImage(
                        model = a.imageUrl,
                        contentDescription = a.animalName,
                        modifier = Modifier.fillMaxSize(),
                        contentScale = ContentScale.Crop
                    )
                    Surface(
                        modifier = Modifier
                            .padding(16.dp)
                            .align(Alignment.BottomStart),
                        shape = RoundedCornerShape(10.dp),
                        color = PrimaryGreen.copy(alpha = 0.9f)
                    ) {
                        Text(
                            text = a.animalType,
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 12.sp,
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp)
                        )
                    }
                }

                // Specifications Grid
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = a.animalName,
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.Bold
                    )

                    Text(
                        text = "${a.breed} • ${a.gender} • ${a.displayLocation}",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(top = 4.dp, bottom = 16.dp)
                    )

                    // Quick Specs Cards
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        SpecCard(title = "Age", value = "${a.age} mos", modifier = Modifier.weight(1f))
                        SpecCard(title = "Weight", value = "%.0f kg".format(a.weight), modifier = Modifier.weight(1f))
                        SpecCard(title = "Milk Yield", value = if (a.milkYield > 0) "%.1f L/day".format(a.milkYield) else "N/A", modifier = Modifier.weight(1f))
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Health & Vaccination Status
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(14.dp),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f))
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Icon(
                                        imageVector = Icons.Filled.HealthAndSafety,
                                        contentDescription = "Health",
                                        tint = PrimaryGreen
                                    )
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text(
                                        text = "Health Status: ${a.healthStatus}",
                                        style = MaterialTheme.typography.titleSmall,
                                        fontWeight = FontWeight.Bold
                                    )
                                }
                                Surface(
                                    shape = RoundedCornerShape(8.dp),
                                    color = if (a.isVaccinated) StatusSuccess else AmberAccent
                                ) {
                                    Text(
                                        text = if (a.isVaccinated) "Vaccinated" else "Not Vaccinated",
                                        color = Color.White,
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.Bold,
                                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                    )
                                }
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Description
                    if (!a.description.isNullOrBlank()) {
                        Text(
                            text = "Description",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = a.description,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                    }

                    // Seller Information Card
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(14.dp),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(14.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Surface(
                                modifier = Modifier.size(48.dp),
                                shape = CircleShape,
                                color = PrimaryGreenLight
                            ) {
                                Box(contentAlignment = Alignment.Center) {
                                    Icon(Icons.Filled.Store, contentDescription = "Seller", tint = Color.White)
                                }
                            }
                            Spacer(modifier = Modifier.width(12.dp))
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = a.sellerName ?: "Verified Livestock Seller",
                                    style = MaterialTheme.typography.titleSmall,
                                    fontWeight = FontWeight.Bold
                                )
                                Text(
                                    text = if (a.sellerVerified) "Verified Farmer / Breeder" else "Community Seller",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(30.dp))
                }
            }
        }
    }
}

@Composable
fun SpecCard(title: String, value: String, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
    ) {
        Column(
            modifier = Modifier.padding(10.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = value,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
        }
    }
}
