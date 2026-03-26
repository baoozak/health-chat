<template>
    <div class="chart-container">
        <Line :data="chartData" :options="chartOptions" />
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
} from 'chart.js'

// 注册 Chart.js 组件
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
)

interface TrendItem {
    date: string
    overall: number
    physical: number
    mental: number
    lifestyle: number
}

const props = defineProps<{
    trends: TrendItem[]
}>()

// 格式化日期标签
const formatLabel = (dateStr: string): string => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return `${date.getMonth() + 1}/${date.getDate()}`
}

// 图表数据
const chartData = computed(() => ({
    labels: props.trends.map(item => formatLabel(item.date)),
    datasets: [
        {
            label: '综合评分',
            data: props.trends.map(item => item.overall),
            borderColor: '#2080f0',
            backgroundColor: 'rgba(32, 128, 240, 0.1)',
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6
        },
        {
            label: '身体健康',
            data: props.trends.map(item => item.physical),
            borderColor: '#18a058',
            backgroundColor: 'rgba(24, 160, 88, 0.1)',
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6
        },
        {
            label: '心理健康',
            data: props.trends.map(item => item.mental),
            borderColor: '#f0a020',
            backgroundColor: 'rgba(240, 160, 32, 0.1)',
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6
        },
        {
            label: '生活方式',
            data: props.trends.map(item => item.lifestyle),
            borderColor: '#d03050',
            backgroundColor: 'rgba(208, 48, 80, 0.1)',
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6
        }
    ]
}))

// 图表配置
const chartOptions: any = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'top',
            labels: {
                boxWidth: 12,
                padding: 16,
                font: {
                    size: 12
                }
            }
        },
        tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
                label: (context: any) => {
                    return `${context.dataset.label}: ${context.parsed.y}分`
                }
            }
        }
    },
    scales: {
        y: {
            min: 0,
            max: 100,
            ticks: {
                stepSize: 20,
                callback: (value: any) => `${value}分`
            },
            grid: {
                color: 'rgba(0, 0, 0, 0.05)'
            }
        },
        x: {
            grid: {
                display: false
            }
        }
    },
    interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false
    }
}
</script>

<style scoped>
.chart-container {
    height: 300px;
    width: 100%;
}
</style>
