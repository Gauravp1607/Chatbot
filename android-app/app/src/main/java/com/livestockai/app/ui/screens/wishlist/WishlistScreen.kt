package com.livestockai.app.ui.screens.wishlist

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.FavoriteBorder
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.livestockai.app.data.repository.MarketplaceRepository
import com.livestockai.app.domain.model.Animal
import com.livestockai.app.ui.components.AnimalCard
import com.livestockai.app.ui.theme.PrimaryGreen
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WishlistScreen(
    marketplaceRepository: MarketplaceRepository,
    onAnimalClick: (Int) -> Unit,
    onNavigateBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    var wishlist by remember { mutableStateOf<List<Animal>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(Unit) {
        val result = marketplaceRepository.getWishlist()
        wishlist = result.getOrDefault(emptyList())
        isLoading = false
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Saved Animals & Wishlist", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        if (isLoading) {
            Box(
                modifier = Modifier.fillMaxSize().padding(padding),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator(color = PrimaryGreen)
            }
        } else if (wishlist.isEmpty()) {
            Box(
                modifier = Modifier.fillMaxSize().padding(padding),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(
                        imageVector = Icons.Filled.FavoriteBorder,
                        contentDescription = "No Wishlist",
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(60.dp)
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "Your Wishlist is Empty",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "Save animals from the marketplace to track them here!",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(top = 4.dp)
                    )
                }
            }
        } else {
            LazyColumn(
                modifier = modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                items(wishlist, key = { it.animalId }) { animal ->
                    AnimalCard(
                        animal = animal,
                        onClick = { onAnimalClick(animal.animalId) },
                        onFavoriteClick = {
                            scope.launch {
                                marketplaceRepository.toggleWishlist(animal.animalId)
                                wishlist = wishlist.filter { it.animalId != animal.animalId }
                            }
                        }
                    )
                }
            }
        }
    }
}
