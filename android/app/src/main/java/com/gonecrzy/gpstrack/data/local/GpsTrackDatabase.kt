package com.gonecrzy.gpstrack.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(
    entities = [MemberEntity::class, PlaceEntity::class],
    version = 1,
    exportSchema = false,
)
abstract class GpsTrackDatabase : RoomDatabase() {
    abstract fun memberDao(): MemberDao
    abstract fun placeDao(): PlaceDao

    companion object {
        fun build(context: Context): GpsTrackDatabase {
            return Room.databaseBuilder(
                context,
                GpsTrackDatabase::class.java,
                "gpstrack.db",
            ).build()
        }
    }
}
