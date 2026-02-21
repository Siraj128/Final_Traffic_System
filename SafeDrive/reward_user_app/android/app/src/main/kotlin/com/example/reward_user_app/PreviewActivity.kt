package com.example.reward_user_app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview

class PreviewActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            SafeDriveApp()
        }
    }
}

@Preview(showBackground = true)
@Composable
fun DefaultPreview() {
    SafeDriveApp()
}
