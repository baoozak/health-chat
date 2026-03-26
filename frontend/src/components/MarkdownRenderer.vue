/**
* Markdown渲染组件
* 使用marked解析Markdown,使用highlight.js进行代码高亮
*/
<template>
    <div class="markdown-content" v-html="renderedContent"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'

const props = defineProps<{
    content: string
}>()

// 配置marked
marked.setOptions({
    breaks: true,  // 支持GFM换行
    gfm: true      // 启用GitHub风格Markdown
})

// 自定义渲染器,添加代码高亮
const renderer = new marked.Renderer()
renderer.code = function ({ text, lang }: { text: string; lang?: string }) {
    if (lang && hljs.getLanguage(lang)) {
        try {
            const highlighted = hljs.highlight(text, { language: lang }).value
            return `<pre><code class="hljs language-${lang}">${highlighted}</code></pre>`
        } catch (err) {
            console.error('代码高亮失败:', err)
        }
    }
    // 如果没有语言或高亮失败,使用自动检测
    const highlighted = hljs.highlightAuto(text).value
    return `<pre><code class="hljs">${highlighted}</code></pre>`
}

marked.use({ renderer })

// 渲染Markdown内容
const renderedContent = computed(() => {
    try {
        return marked(props.content) as string
    } catch (error) {
        console.error('Markdown渲染失败:', error)
        return props.content
    }
})
</script>

<style scoped>
.markdown-content {
    line-height: 1.6;
    color: #333;
}

/* 标题样式 */
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
    margin-top: 16px;
    margin-bottom: 8px;
    font-weight: 600;
    line-height: 1.25;
}

.markdown-content :deep(h1) {
    font-size: 1.8em;
    border-bottom: 1px solid #eaecef;
    padding-bottom: 8px;
}

.markdown-content :deep(h2) {
    font-size: 1.5em;
    border-bottom: 1px solid #eaecef;
    padding-bottom: 6px;
}

.markdown-content :deep(h3) {
    font-size: 1.25em;
}

/* 段落样式 */
.markdown-content :deep(p) {
    margin-bottom: 12px;
}

/* 列表样式 */
.markdown-content :deep(ul),
.markdown-content :deep(ol) {
    margin-bottom: 12px;
    padding-left: 24px;
}

.markdown-content :deep(li) {
    margin-bottom: 4px;
}

/* 代码块样式 */
.markdown-content :deep(pre) {
    background-color: #1e1e1e;
    border-radius: 6px;
    padding: 16px;
    overflow-x: auto;
    margin-bottom: 12px;
}

.markdown-content :deep(code) {
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 0.9em;
}

/* 行内代码样式 */
.markdown-content :deep(p code),
.markdown-content :deep(li code) {
    background-color: #f6f8fa;
    padding: 2px 6px;
    border-radius: 3px;
    color: #e83e8c;
}

/* 引用样式 */
.markdown-content :deep(blockquote) {
    border-left: 4px solid #dfe2e5;
    padding-left: 16px;
    margin-left: 0;
    margin-bottom: 12px;
    color: #6a737d;
}

/* 表格样式 */
.markdown-content :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 12px;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
    border: 1px solid #dfe2e5;
    padding: 8px 12px;
}

.markdown-content :deep(th) {
    background-color: #f6f8fa;
    font-weight: 600;
}

/* 链接样式 */
.markdown-content :deep(a) {
    color: #0366d6;
    text-decoration: none;
}

.markdown-content :deep(a:hover) {
    text-decoration: underline;
}

/* 水平线样式 */
.markdown-content :deep(hr) {
    border: none;
    border-top: 1px solid #eaecef;
    margin: 16px 0;
}

/* 图片样式 */
.markdown-content :deep(img) {
    max-width: 100%;
    height: auto;
    border-radius: 4px;
}
</style>
