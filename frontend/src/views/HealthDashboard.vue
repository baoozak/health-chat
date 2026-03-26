<template>
    <div class="health-dashboard">
        <NSpace vertical :size="24">
            <!-- 页面标题 -->
            <NPageHeader title="🏥 我的健康状态" subtitle="基于AI的全面健康分析">
                <template #extra>
                    <NButton quaternary @click="goBack" style="margin-right: 8px">
                        <template #icon>
                            <NIcon>
                                <ArrowBack />
                            </NIcon>
                        </template>
                        返回聊天
                    </NButton>
                    <NButton quaternary @click="showHistoryDrawer = true; loadHealthHistory()"
                        style="margin-right: 8px">
                        <template #icon>
                            <NIcon>
                                <TimeOutline />
                            </NIcon>
                        </template>
                        历史报告
                    </NButton>
                    <NButton type="primary" :loading="loading" @click="handleGenerateReport">
                        <template #icon>
                            <NIcon>
                                <RefreshOutline />
                            </NIcon>
                        </template>
                        {{ report ? '重新生成报告' : '生成健康报告' }}
                    </NButton>
                </template>
            </NPageHeader>

            <!-- 加载状态 -->
            <NSpin v-if="loading" :size="60">
                <template #description>
                    正在分析您的健康数据，请稍候...
                </template>
            </NSpin>

            <!-- 数据不足提示 -->
            <NAlert v-else-if="!loading && !report && !error" type="info" title="数据不足">
                您还没有足够的健康咨询数据。请先进行至少一次健康咨询，然后再生成报告。
            </NAlert>

            <!-- 错误提示 -->
            <NAlert v-else-if="error" type="error" title="生成失败">
                {{ error }}
            </NAlert>

            <!-- 健康报告内容 -->
            <template v-else-if="report">
                <!-- 综合健康评分 -->
                <NCard title="📊 综合健康评分" :bordered="false">
                    <NSpace vertical>
                        <div class="score-display">
                            <NProgress type="circle" :percentage="report.health_score?.overall || 0"
                                :color="getScoreColor(report.health_score?.overall || 0)" :height="120">
                                <div class="score-text">
                                    <div class="score-value">{{ report.health_score?.overall || 0 }}</div>
                                    <div class="score-label">{{ getScoreLevel(report.health_score?.overall || 0) }}
                                    </div>
                                </div>
                            </NProgress>
                        </div>

                        <NGrid :cols="3" :x-gap="12">
                            <NGridItem>
                                <NStatistic label="身体健康" :value="report.health_score?.physical || 0" />
                            </NGridItem>
                            <NGridItem>
                                <NStatistic label="心理健康" :value="report.health_score?.mental || 0" />
                            </NGridItem>
                            <NGridItem>
                                <NStatistic label="生活方式" :value="report.health_score?.lifestyle || 0" />
                            </NGridItem>
                        </NGrid>
                    </NSpace>
                </NCard>

                <!-- 风险评估 -->
                <NCard title="⚠️ 风险评估" :bordered="false">
                    <NSpace vertical :size="16">
                        <!-- 高风险 -->
                        <div v-if="report.risk_assessment?.high_risk?.length">
                            <NText strong style="color: #d03050;">高风险项目</NText>
                            <NList bordered style="margin-top: 8px;">
                                <NListItem v-for="(item, index) in report.risk_assessment.high_risk" :key="index">
                                    <NTag type="error" size="small">{{ item }}</NTag>
                                </NListItem>
                            </NList>
                        </div>

                        <!-- 中风险 -->
                        <div v-if="report.risk_assessment?.medium_risk?.length">
                            <NText strong style="color: #f0a020;">中风险项目</NText>
                            <NList bordered style="margin-top: 8px;">
                                <NListItem v-for="(item, index) in report.risk_assessment.medium_risk" :key="index">
                                    <NTag type="warning" size="small">{{ item }}</NTag>
                                </NListItem>
                            </NList>
                        </div>

                        <!-- 低风险 -->
                        <div v-if="report.risk_assessment?.low_risk?.length">
                            <NText strong style="color: #18a058;">低风险项目</NText>
                            <NList bordered style="margin-top: 8px;">
                                <NListItem v-for="(item, index) in report.risk_assessment.low_risk" :key="index">
                                    <NTag type="success" size="small">{{ item }}</NTag>
                                </NListItem>
                            </NList>
                        </div>

                        <NEmpty v-if="!hasRisks" description="暂无风险项目" />
                    </NSpace>
                </NCard>

                <!-- 个性化建议 -->
                <NCard title="💡 个性化建议" :bordered="false">
                    <NTabs type="line">
                        <NTabPane name="diet" tab="🥗 饮食建议">
                            <NList v-if="report.recommendations?.diet?.length" bordered>
                                <NListItem v-for="(item, index) in report.recommendations.diet" :key="index">
                                    <NText type="success">{{ item }}</NText>
                                </NListItem>
                            </NList>
                            <NEmpty v-else description="暂无饮食建议" />
                        </NTabPane>

                        <NTabPane name="exercise" tab="🏃 运动建议">
                            <NList v-if="report.recommendations?.exercise?.length" bordered>
                                <NListItem v-for="(item, index) in report.recommendations.exercise" :key="index">
                                    <NText type="info">{{ item }}</NText>
                                </NListItem>
                            </NList>
                            <NEmpty v-else description="暂无运动建议" />
                        </NTabPane>

                        <NTabPane name="lifestyle" tab="😴 生活方式">
                            <NList v-if="report.recommendations?.lifestyle?.length" bordered>
                                <NListItem v-for="(item, index) in report.recommendations.lifestyle" :key="index">
                                    <NText type="primary">{{ item }}</NText>
                                </NListItem>
                            </NList>
                            <NEmpty v-else description="暂无生活方式建议" />
                        </NTabPane>

                        <NTabPane name="medical" tab="🏥 就医建议">
                            <NList v-if="report.recommendations?.medical?.length" bordered>
                                <NListItem v-for="(item, index) in report.recommendations.medical" :key="index">
                                    <NText type="warning">{{ item }}</NText>
                                </NListItem>
                            </NList>
                            <NEmpty v-else description="暂无就医建议" />
                        </NTabPane>
                    </NTabs>
                </NCard>

                <!-- 综合分析 -->
                <NCard title="🤖 综合分析" :bordered="false">
                    <div v-if="report.ai_comprehensive_analysis" class="ai-analysis-content">
                        <MarkdownRenderer :content="report.ai_comprehensive_analysis" />
                    </div>
                    <NEmpty v-else description="暂无综合分析" />
                </NCard>
            </template>

            <!-- 健康趋势 -->
            <NCard title="📈 评分趋势" :bordered="false">
                <template #header-extra>
                    <NText depth="3" style="font-size: 12px;">
                        基于最近的 {{ trends?.report_count || 0 }} 份历史报告
                    </NText>
                </template>
                <NSpin v-if="trendsLoading" size="small" />
                <template v-else-if="trends && trends.report_count > 1">
                    <HealthTrendChart :trends="trends.trends" />
                </template>
                <NEmpty v-else description="需要至少2份报告才能显示趋势图" />
            </NCard>
        </NSpace>

        <!-- 历史报告抽屉 -->
        <NDrawer v-model:show="showHistoryDrawer" :width="400" placement="right">
            <NDrawerContent title="📋 历史报告" closable>
                <NSpin v-if="historyLoading" size="small"
                    style="display: flex; justify-content: center; padding: 40px;" />
                <template v-else-if="history.length">
                    <NList hoverable clickable>
                        <NListItem v-for="(item, index) in history" :key="index" @click="viewHistoryReport(item)">
                            <NThing>
                                <template #header>
                                    <NSpace align="center" :size="8">
                                        <NProgress type="circle" :percentage="item.health_score?.overall || 0"
                                            :color="getScoreColor(item.health_score?.overall || 0)"
                                            :show-indicator="false" :stroke-width="12"
                                            style="width: 24px; height: 24px;" />
                                        <NText strong>{{ item.health_score?.overall || 0 }}分</NText>
                                        <NTag :type="getScoreTagType(item.health_score?.overall || 0)" size="small">
                                            {{ getScoreLevel(item.health_score?.overall || 0) }}
                                        </NTag>
                                    </NSpace>
                                </template>
                                <template #description>
                                    <NSpace :size="12">
                                        <NText depth="3" style="font-size: 12px;">身体: {{ item.health_score?.physical ||
                                            0 }}</NText>
                                        <NText depth="3" style="font-size: 12px;">心理: {{ item.health_score?.mental || 0
                                        }}</NText>
                                        <NText depth="3" style="font-size: 12px;">生活: {{ item.health_score?.lifestyle ||
                                            0 }}</NText>
                                    </NSpace>
                                </template>
                                <template #header-extra>
                                    <NText depth="3" style="font-size: 12px;">
                                        {{ formatDateTime(item.generated_at) }}
                                    </NText>
                                </template>
                            </NThing>
                        </NListItem>
                    </NList>
                </template>
                <NEmpty v-else description="暂无历史报告" style="padding: 40px 0;" />
            </NDrawerContent>
        </NDrawer>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { RefreshOutline, ArrowBack, TimeOutline } from '@vicons/ionicons5'
import {
    NSpace,
    NPageHeader,
    NButton,
    NIcon,
    NSpin,
    NAlert,
    NCard,
    NProgress,
    NEmpty,
    NTag,
    NText,
    NList,
    NListItem,
    NTabs,
    NTabPane,
    NThing,
    NDrawer,
    NDrawerContent,
    useMessage
} from 'naive-ui'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'
import HealthTrendChart from '../components/HealthTrendChart.vue'
import { healthApi } from '../api/health'
import type { HealthReport } from '../types'

const router = useRouter()
const message = useMessage()
const loading = ref(false)
const error = ref('')
const report = ref<HealthReport | null>(null)
const showHistoryDrawer = ref(false)

// 健康趋势相关
const trendsLoading = ref(false)
const trends = ref<any>(null)

// 历史报告相关
const historyLoading = ref(false)
const history = ref<HealthReport[]>([])

// 计算属性
const hasRisks = computed(() => {
    const risks = report.value?.risk_assessment
    return risks && (
        (risks.high_risk?.length || 0) > 0 ||
        (risks.medium_risk?.length || 0) > 0 ||
        (risks.low_risk?.length || 0) > 0
    )
})

// 获取评分颜色
const getScoreColor = (score: number) => {
    if (score >= 85) return '#18a058'
    if (score >= 70) return '#2080f0'
    if (score >= 60) return '#f0a020'
    return '#d03050'
}

// 获取评分等级
const getScoreLevel = (score: number) => {
    if (score >= 85) return '优秀'
    if (score >= 70) return '良好'
    if (score >= 60) return '一般'
    return '需改善'
}

// 加载健康报告
const loadHealthReport = async () => {
    try {
        loading.value = true
        error.value = ''

        const response = await healthApi.getHealthAnalysis()
        if (response.success) {
            report.value = response.data
            if (response.cached) {
                message.info('已加载缓存的健康报告')
            } else {
                message.success('健康报告生成成功')
            }
        }
    } catch (err: any) {
        console.error('加载健康报告失败:', err)
        if (err.response?.status === 400) {
            error.value = '数据不足，请至少进行一次健康咨询后再生成报告'
        } else {
            error.value = err.response?.data?.detail || '加载失败，请稍后重试'
        }
    } finally {
        loading.value = false
    }
}

// 返回聊天页面
const goBack = () => {
    router.push('/')
}

// 生成新报告
const handleGenerateReport = async () => {
    try {
        loading.value = true
        error.value = ''

        const response = await healthApi.generateHealthAnalysis()
        if (response.success) {
            report.value = response.data
            message.success('健康报告已重新生成')
            // 刷新趋势数据和历史报告
            loadHealthTrends()
            loadHealthHistory()
        }
    } catch (err: any) {
        console.error('生成健康报告失败:', err)
        if (err.response?.status === 400) {
            error.value = '数据不足，请至少进行一次健康咨询后再生成报告'
            message.error(error.value)
        } else {
            error.value = err.response?.data?.detail || '生成失败，请稍后重试'
            message.error(error.value)
        }
    } finally {
        loading.value = false
    }
}

// 加载健康趋势
const loadHealthTrends = async () => {
    try {
        trendsLoading.value = true
        const response = await healthApi.getHealthTrends()
        if (response.success) {
            trends.value = response.data
        }
    } catch (err: any) {
        console.error('加载健康趋势失败:', err)
    } finally {
        trendsLoading.value = false
    }
}

// 加载历史报告
const loadHealthHistory = async () => {
    try {
        historyLoading.value = true
        const response = await healthApi.getHealthHistory(10)
        if (response.success) {
            history.value = response.data
        }
    } catch (err: any) {
        console.error('加载历史报告失败:', err)
    } finally {
        historyLoading.value = false
    }
}

// 查看历史报告
const viewHistoryReport = (item: HealthReport) => {
    report.value = item
    showHistoryDrawer.value = false
    message.info('已切换到历史报告')
    // 滚动到页面顶部
    window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 获取评分标签类型
const getScoreTagType = (score: number): 'success' | 'info' | 'warning' | 'error' => {
    if (score >= 85) return 'success'
    if (score >= 70) return 'info'
    if (score >= 60) return 'warning'
    return 'error'
}

// 格式化日期时间
const formatDateTime = (dateStr: string | undefined) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN')
}

// 组件挂载时加载数据
onMounted(() => {
    loadHealthReport()
    loadHealthTrends()
    loadHealthHistory()
})
</script>

<style scoped>
.health-dashboard {
    padding: 24px;
    max-width: 1200px;
    margin: 0 auto;
}

.score-display {
    display: flex;
    justify-content: center;
    padding: 24px 0;
}

.score-text {
    text-align: center;
}

.score-value {
    font-size: 32px;
    font-weight: bold;
    line-height: 1;
}

.score-label {
    font-size: 14px;
    color: #666;
    margin-top: 4px;
}

.indicator-value {
    font-size: 24px;
    font-weight: bold;
    color: #18a058;
}

.trend-value {
    font-size: 20px;
    font-weight: bold;
    color: #2080f0;
}

.trend-up {
    font-size: 20px;
    font-weight: bold;
    color: #18a058;
}

.trend-down {
    font-size: 20px;
    font-weight: bold;
    color: #d03050;
}

.trend-stable {
    font-size: 20px;
    font-weight: bold;
    color: #909399;
}

.ai-analysis-content {
    line-height: 1.8;
}
</style>