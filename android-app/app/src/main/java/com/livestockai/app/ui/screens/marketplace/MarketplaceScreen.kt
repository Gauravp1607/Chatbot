package com.livestockai.app.ui.screens.marketplace

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.livestockai.app.ui.components.AnimalCard
import com.livestockai.app.ui.components.MarketplaceSearchBar
import com.livestockai.app.ui.theme.PrimaryGreen

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MarketplaceScreen(
    viewModel: MarketplaceViewModel,
    onAnimalClick: (Int) -> Unit,
    onAddListingClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.uiState.collectAsState()
    var showFilterSheet by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Livestock Marketplace",
                        fontWeight = FontWeight.Bold
                    )
                },
                actions = {
                    IconButton(onClick = { viewModel.fetchAnimals() }) {
                        Icon(Icons.Filled.Refresh, contentDescription = "Refresh")
                    }
                }
            )
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = onAddListingClick,
                containerColor = PrimaryGreen,
                contentColor = Color.White,
                shape = RoundedCornerShape(16.dp)
            ) {
                Icon(Icons.Filled.Add, contentDescription = "Sell Animal")
                Spacer(modifier = Modifier.width(8.dp))
                Text(text = "Sell Livestock", fontWeight = FontWeight.Bold)
            }
        }
    ) { padding ->
        Column(
            modifier = modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Search Bar & Filter Action
            MarketplaceSearchBar(
                query = uiState.searchQuery,
                onQueryChange = { viewModel.onSearchQueryChanged(it) },
                onSearch = { viewModel.fetchAnimals() },
                onFilterClick = { showFilterSheet = true }
            )

            // Category Filter Chips
            LazyRow(
                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 6.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                item {
                    FilterChip(
                        selected = uiState.selectedCategory == null,
                        onClick = { viewModel.onCategorySelected(null) },
                        label = { Text("All") },
                        colors = FilterChipDefaults.filterChipColors(
                            selectedContainerColor = PrimaryGreen,
                            selectedLabelColor = Color.White
                        )
                    )
                }

                items(uiState.categories) { category ->
                    FilterChip(
                        selected = uiState.selectedCategory == category,
                        onClick = { viewModel.onCategorySelected(category) },
                        label = { Text(category) },
                        colors = FilterChipDefaults.filterChipColors(
                            selectedContainerColor = PrimaryGreen,
                            selectedLabelColor = Color.White
                        )
                    )
                }
            }

            Spacer(modifier = Modifier.height(4.dp))

            // Grid Content
            if (uiState.isLoading) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(color = PrimaryGreen)
                }
            } else if (uiState.animals.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            text = "No livestock found",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = "Try adjusting your search query or filters.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.padding(top = 4.dp)
                        )
                    }
                }
            } else {
                LazyVerticalGrid(
                    columns = GridCells.Fixed(1),
                    contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 8.dp, bottom = 80.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp),
                    modifier = Modifier.fillMaxSize()
                ) {
                    items(uiState.animals, key = { it.animalId }) { animal ->
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

    // Filter Bottom Sheet
    if (showFilterSheet) {
        ModalBottomSheet(
            onDismissRequest = { showFilterSheet = false },
            sheetState = rememberModalBottomSheetState()
        ) {
            FilterBottomSheetContent(
                currentMinPrice = uiState.minPrice,
                currentMaxPrice = uiState.maxPrice,
                currentVaccinatedOnly = uiState.vaccinatedOnly,
                currentSortBy = uiState.sortBy,
                onApply = { min, max, vacc, sort ->
                    viewModel.applyFilters(min, max, vacc, sort)
                    showFilterSheet = false
                },
                onReset = {
                    viewModel.applyFilters(null, null, false, "newest")
                    showFilterSheet = false
                }
            )
        }
    }
}

@Composable
fun FilterBottomSheetContent(
    currentMinPrice: Double?,
    currentMaxPrice: Double?,
    currentVaccinatedOnly: Boolean,
    currentSortBy: String,
    onApply: (Double?, Double?, Boolean, String) -> Unit,
    onReset: () -> Unit
) {
    var minPriceText by remember { mutableStateOf(currentMinPrice?.toString() ?: "") }
    var maxPriceText by remember { mutableStateOf(currentMaxPrice?.toString() ?: "") }
    var vaccinatedOnly by remember { mutableStateOf(currentVaccinatedOnly) }
    var sortBy by remember { mutableStateOf(currentSortBy) }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(20.dp)
    ) {
        Text(
            text = "Filter & Sort Listings",
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Sort By
        Text(
            text = "Sort By",
            style = MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.SemiBold
        )
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            listOf(
                "newest" to "Newest",
                "price_asc" to "Price Low-High",
                "price_desc" to "Price High-Low"
            ).forEach { (key, label) ->
                FilterChip(
                    selected = sortBy == key,
                    onClick = { sortBy = key },
                    label = { Text(label) },
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = PrimaryGreen,
                        selectedLabelColor = Color.White
                    )
                )
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // Price Range
        Text(
            text = "Price Range (₹)",
            style = MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.SemiBold
        )
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            OutlinedTextField(
                value = minPriceText,
                onValueChange = { minPriceText = it },
                label = { Text("Min Price") },
                modifier = Modifier.weight(1f),
                shape = RoundedCornerShape(12.dp)
            )
            OutlinedTextField(
                value = maxPriceText,
                onValueChange = { maxPriceText = it },
                label = { Text("Max Price") },
                modifier = Modifier.weight(1f),
                shape = RoundedCornerShape(12.dp)
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Vaccinated Only Toggle
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(
                text = "Show Verified Vaccinated Only",
                style = MaterialTheme.typography.bodyMedium
            )
            Switch(
                checked = vaccinatedOnly,
                onCheckedChange = { vaccinatedOnly = it },
                colors = SwitchDefaults.colors(checkedThumbColor = PrimaryGreen)
            )
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            OutlinedButton(
                onClick = onReset,
                modifier = Modifier.weight(1f),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("Reset")
            }

            Button(
                onClick = {
                    val min = minPriceText.toDoubleOrNull()
                    val max = maxPriceText.toDoubleOrNull()
                    onApply(min, max, vaccinatedOnly, sortBy)
                },
                modifier = Modifier.weight(1f),
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(containerColor = PrimaryGreen)
            ) {
                Text("Apply Filters", fontWeight = FontWeight.Bold)
            }
        }

        Spacer(modifier = Modifier.height(24.dp))
    }
}
