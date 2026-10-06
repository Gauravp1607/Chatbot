package com.livestockai.app

import android.app.Application

class LivestockApplication : Application() {

    override fun onCreate() {
        super.onCreate()
        instance = this
    }

    companion object {
        lateinit var instance: LivestockApplication
            private set
    }
}
