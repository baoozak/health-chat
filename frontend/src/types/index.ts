/**
 * 类型定义文件
 * 定义应用中使用的TypeScript接口和类型
 */
/**
 * 类型定义文件
 * 定义应用中使用的TypeScript接口和类型
 */

/**
 * 消息类型枚举
 */
export enum MessageType {
  USER = 'user',    // 用户消息
  AI = 'ai',        // AI消息
  FILE = 'file'     // 文件消息
}

/**
 * 文件信息接口
 */
export interface FileInfo {
  name: string      // 文件名
  size: number      // 文件大小(字节)
  type: string      // 文件MIME类型
}

/**
 * 消息接口
 */
export interface Message {
  id: string          // 消息唯一ID
  type: MessageType   // 消息类型
  content: string     // 消息内容  
  timestamp: number   // 时间戳
  file?: FileInfo     // 文件信息(可选)
  image_data?: string  // 图片base64数据(可选)
  image_filename?: string  // 图片文件名(可选)
  image_mime_type?: string  // 图片MIME类型(可选)
}

/**
 * 健康评分接口
 */
export interface HealthScore {
  overall: number      // 综合评分
  physical: number     // 身体健康评分
  mental: number       // 心理健康评分
  lifestyle: number    // 生活方式评分
}

/**
 * 风险评估接口
 */
export interface RiskAssessment {
  high_risk: string[]     // 高风险项目
  medium_risk: string[]   // 中风险项目
  low_risk: string[]      // 低风险项目
}

/**
 * 健康趋势接口
 */
export interface HealthTrend {
  direction: string    // 方向 (up/down/stable)
  change: number       // 变化量
  period: string       // 时间周期
}

/**
 * 健康建议接口
 */
export interface HealthRecommendations {
  diet: string[]       // 饮食建议
  exercise: string[]   // 运动建议
  lifestyle: string[]  // 生活方式建议
  medical: string[]    // 就医建议
}

/**
 * 健康报告接口
 */
export interface HealthReport {
  report_id?: string                              // 报告ID
  generated_at?: string                           // 生成时间
  health_score: HealthScore                       // 健康评分
  risk_assessment: RiskAssessment                 // 风险评估
  trends: Record<string, HealthTrend>            // 趋势分析
  recommendations: HealthRecommendations          // 个性化建议
  ai_comprehensive_analysis?: string             // 综合分析
}
