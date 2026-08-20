<script setup>
import { ref } from 'vue'
const weatherData = ref(null);
const loading = ref(false);
async function fetchData() {
    if (loading.value) {
        return
    }
    loading.value = true;
    weatherData.value = null
    const res = await fetch(
        `api/gadget/weather/`
    );
    weatherData.value = await res.json();
    loading.value = false;
}
fetchData();
</script>

<template>
    <div @click="fetchData">
        <div v-if="weatherData">
            <div class="weather-wrapper">
                <div v-for="reading in weatherData" :key="reading.id" class="weather-entry border border-light rounded p-1">
                    <div class="text-center"><img v-bind:src="reading.sun" class="rounded weather-icon" v-bind:alt="reading.sun_id"></div>
                    <div class="text-center fw-bold">{{ reading.temperature }}</div>
                    <div class="text-center fw-light">{{ reading.hour }}</div>
                </div>
            </div>
        </div>
        <div v-else>
            <span>No data.</span>
        </div>
    </div>
</template>

<style>
.weather-wrapper {
    display: flex;
    flex-direction: row;
    gap: 0.3em;
    cursor: pointer;
}

.weather-entry {
    display: flex;
    flex-direction: column;
    background: rgba(90, 90, 90, 0.5);
}
.weather-icon {
    max-width: 50px;
}
</style>

<script>

import { defineComponent } from 'vue';

export default defineComponent({
    name: 'WeatherGadget'
});

</script>