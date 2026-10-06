package com.livestockai.app.data.repository

import com.livestockai.app.data.api.ApiClient
import com.livestockai.app.data.api.dto.OrderDto
import com.livestockai.app.data.local.TokenManager
import com.livestockai.app.domain.model.Order
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class OrderRepository(private val tokenManager: TokenManager) {

    private val apiService get() = ApiClient.getApiService(tokenManager)

    suspend fun getOrders(): Result<List<Order>> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getOrders()
            if (response.isSuccessful && response.body()?.status == "success") {
                val dtos = response.body()?.orders ?: emptyList()
                return@withContext Result.success(dtos.map { it.toDomain() })
            }
            Result.failure(Exception("Failed to fetch orders"))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun createOrder(animalId: Int): Result<Pair<Int, String>> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.createOrder(mapOf("animal_id" to animalId))
            if (response.isSuccessful && response.body()?.status == "success") {
                val body = response.body()!!
                return@withContext Result.success(Pair(body.orderId, body.amountPayable))
            }
            val msg = response.body()?.message ?: "Order creation failed"
            Result.failure(Exception(msg))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    private fun OrderDto.toDomain(): Order {
        return Order(
            orderId = orderId,
            animalId = animalId,
            animalName = animalName ?: "$animalType $breed",
            animalType = animalType ?: "Livestock",
            breed = breed ?: "",
            price = price,
            buyerPayableAmount = buyerPayableAmount,
            orderStatus = orderStatus,
            paymentStatus = paymentStatus,
            imageUrl = ApiClient.getImageUrl(imageUrl),
            sellerName = sellerName,
            buyerName = buyerName,
            createdAt = createdAt
        )
    }
}
