import Foundation
import AppKit

class ReportExporter {
    static let shared = ReportExporter()

    // MARK: - 导出关键词检索报告

    func exportKeywordSearchReport(_ results: KeywordSearchResponse, format: ExportFormat = .html) -> URL? {
        switch format {
        case .html:
            return exportKeywordSearchHTML(results)
        case .markdown:
            return exportKeywordSearchMarkdown(results)
        case .text:
            return exportKeywordSearchText(results)
        }
    }

    private func exportKeywordSearchHTML(_ results: KeywordSearchResponse) -> URL? {
        let html = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>关键词检索报告 - \(results.keyword)</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                    line-height: 1.6;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f5f5f5;
                }
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 12px;
                    margin-bottom: 20px;
                }
                .keyword {
                    font-size: 32px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                .stats {
                    font-size: 18px;
                    opacity: 0.9;
                }
                .section {
                    background: white;
                    padding: 20px;
                    border-radius: 12px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                .section-title {
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 15px;
                    color: #333;
                }
                .item {
                    padding: 15px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    margin-bottom: 10px;
                }
                .timestamp {
                    display: inline-block;
                    background: #667eea;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                    margin-right: 10px;
                }
                .filename {
                    font-weight: bold;
                    color: #333;
                }
                .context {
                    color: #666;
                    margin-top: 8px;
                }
                .tag {
                    display: inline-block;
                    background: #e3f2fd;
                    color: #1976d2;
                    padding: 4px 12px;
                    border-radius: 16px;
                    margin-right: 8px;
                    font-size: 14px;
                }
                .footer {
                    text-align: center;
                    color: #999;
                    margin-top: 40px;
                    padding: 20px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="keyword">关键词：\(results.keyword)</div>
                <div class="stats">找到 \(results.totalMentions) 处提及</div>
            </div>

            \(results.relatedKeywords.isEmpty ? "" : """
            <div class="section">
                <div class="section-title">相关关键词</div>
                <div>
                    \(results.relatedKeywords.map { "<span class='tag'>\($0)</span>" }.joined())
                </div>
            </div>
            """)

            \(results.videoTimestamps.isEmpty ? "" : """
            <div class="section">
                <div class="section-title">视频中的提及 (\(results.videoTimestamps.count))</div>
                \(results.videoTimestamps.map { timestamp in """
                <div class="item">
                    <div>
                        <span class="timestamp">\(timestamp.timestamp)</span>
                        <span class="filename">\(timestamp.filename)</span>
                    </div>
                    <div class="context">\(timestamp.context)</div>
                </div>
                """ }.joined())
            </div>
            """)

            \(results.audioTimestamps.isEmpty ? "" : """
            <div class="section">
                <div class="section-title">音频中的提及 (\(results.audioTimestamps.count))</div>
                \(results.audioTimestamps.map { timestamp in """
                <div class="item">
                    <div>
                        <span class="timestamp">\(timestamp.timestamp)</span>
                        <span class="filename">\(timestamp.filename)</span>
                    </div>
                    <div class="context">\(timestamp.context)</div>
                </div>
                """ }.joined())
            </div>
            """)

            \(results.documents.isEmpty ? "" : """
            <div class="section">
                <div class="section-title">文档中的提及 (\(results.documents.count))</div>
                \(results.documents.map { doc in """
                <div class="item">
                    <div class="filename">\(doc.filename)</div>
                    \(doc.matches.map { match in """
                    <div class="context">
                        \(match.paragraph != nil ? "第\(match.paragraph!)段：" : "")\(match.context)
                    </div>
                    """ }.joined())
                </div>
                """ }.joined())
            </div>
            """)

            <div class="footer">
                <p>FieldMind 乡村调研平台</p>
                <p>生成时间：\(Date().formatted(date: .long, time: .shortened))</p>
            </div>
        </body>
        </html>
        """

        return saveToFile(content: html, filename: "关键词检索_\(results.keyword)_\(timestamp()).html")
    }

    private func exportKeywordSearchMarkdown(_ results: KeywordSearchResponse) -> URL? {
        var markdown = """
        # 关键词检索报告

        **关键词**: \(results.keyword)
        **找到**: \(results.totalMentions) 处提及
        **生成时间**: \(Date().formatted(date: .long, time: .shortened))

        ---

        """

        if !results.relatedKeywords.isEmpty {
            markdown += """
            ## 相关关键词

            \(results.relatedKeywords.map { "- \($0)" }.joined(separator: "\n"))

            ---

            """
        }

        if !results.videoTimestamps.isEmpty {
            markdown += """
            ## 视频中的提及 (\(results.videoTimestamps.count))

            \(results.videoTimestamps.map { timestamp in """
            ### \(timestamp.filename)
            - **时间点**: \(timestamp.timestamp)
            - **内容**: \(timestamp.context)

            """ }.joined(separator: "\n"))

            ---

            """
        }

        if !results.audioTimestamps.isEmpty {
            markdown += """
            ## 音频中的提及 (\(results.audioTimestamps.count))

            \(results.audioTimestamps.map { timestamp in """
            ### \(timestamp.filename)
            - **时间点**: \(timestamp.timestamp)
            - **内容**: \(timestamp.context)

            """ }.joined(separator: "\n"))

            ---

            """
        }

        if !results.documents.isEmpty {
            markdown += """
            ## 文档中的提及 (\(results.documents.count))

            \(results.documents.map { doc in """
            ### \(doc.filename)

            \(doc.matches.enumerated().map { index, match in """
            **\(index + 1).** \(match.paragraph != nil ? "第\(match.paragraph!)段：" : "")\(match.context)
            """ }.joined(separator: "\n"))

            """ }.joined(separator: "\n"))
            """
        }

        markdown += """

        ---

        *FieldMind 乡村调研平台*
        """

        return saveToFile(content: markdown, filename: "关键词检索_\(results.keyword)_\(timestamp()).md")
    }

    private func exportKeywordSearchText(_ results: KeywordSearchResponse) -> URL? {
        var text = """
        关键词检索报告
        =====================================

        关键词: \(results.keyword)
        找到: \(results.totalMentions) 处提及
        生成时间: \(Date().formatted(date: .long, time: .shortened))

        =====================================

        """

        if !results.relatedKeywords.isEmpty {
            text += """

            相关关键词:
            \(results.relatedKeywords.joined(separator: ", "))

            =====================================

            """
        }

        if !results.videoTimestamps.isEmpty {
            text += """

            视频中的提及 (\(results.videoTimestamps.count)):
            -------------------------------------

            \(results.videoTimestamps.enumerated().map { index, timestamp in """
            \(index + 1). [\(timestamp.timestamp)] \(timestamp.filename)
               \(timestamp.context)

            """ }.joined())

            """
        }

        return saveToFile(content: text, filename: "关键词检索_\(results.keyword)_\(timestamp()).txt")
    }

    // MARK: - 导出文创分析报告

    func exportCreativeAnalysisReport(_ results: CreativeAnalysisResponse, format: ExportFormat = .html) -> URL? {
        switch format {
        case .html:
            return exportCreativeAnalysisHTML(results)
        case .markdown:
            return exportCreativeAnalysisMarkdown(results)
        case .text:
            return exportCreativeAnalysisText(results)
        }
    }

    private func exportCreativeAnalysisHTML(_ results: CreativeAnalysisResponse) -> URL? {
        let html = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>在地文创分析报告</title>
            <style>
                body { font-family: -apple-system, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
                .header { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; }
                .title { font-size: 32px; font-weight: bold; margin-bottom: 10px; }
                .section { background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
                .section-title { font-size: 24px; font-weight: bold; margin-bottom: 15px; color: #333; }
                .possibility { padding: 20px; background: #f8f9fa; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #f5576c; }
                .score { display: inline-block; background: #4caf50; color: white; padding: 8px 16px; border-radius: 8px; font-size: 24px; font-weight: bold; float: right; }
                .score.medium { background: #ff9800; }
                .score.low { background: #f44336; }
                .idea-title { font-size: 20px; font-weight: bold; color: #333; margin-bottom: 10px; }
                .description { color: #666; margin-bottom: 10px; }
                .innovation { background: #fff3e0; padding: 10px; border-radius: 6px; margin: 10px 0; }
                .detail-item { margin: 10px 0; }
                .detail-label { font-weight: bold; color: #555; }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">在地文创分析报告</div>
                <div>关键词: \(results.keywords.joined(separator: ", "))</div>
            </div>

            \(!results.culturalElements.isEmpty ? """
            <div class="section">
                <div class="section-title">文化元素</div>
                \(results.culturalElements.map { element in """
                <div class="possibility">
                    <h3>\(element.element)</h3>
                    <p><strong>独特性:</strong> \(element.uniqueness)</p>
                    <p><strong>文化意义:</strong> \(element.culturalMeaning)</p>
                </div>
                """ }.joined())
            </div>
            """ : "")

            <div class="section">
                <div class="section-title">创意可能性 (\(results.creativePossibilities.count))</div>
                \(results.creativePossibilities.map { p in """
                <div class="possibility">
                    <span class="score \(p.feasibilityScore >= 70 ? "" : p.feasibilityScore >= 50 ? "medium" : "low")">\(p.feasibilityScore)</span>
                    <div class="idea-title">\(p.idea)</div>
                    <div class="description">\(p.description)</div>
                    <div class="innovation">💡 创新点: \(p.innovationPoint)</div>
                    <div class="detail-item"><span class="detail-label">目标人群:</span> \(p.targetAudience)</div>
                    <div class="detail-item"><span class="detail-label">市场潜力:</span> \(p.marketPotential)</div>
                    <div class="detail-item"><span class="detail-label">所需资源:</span> \(p.requiredResources.joined(separator: ", "))</div>
                    <div class="detail-item"><span class="detail-label">风险点:</span> \(p.risks.joined(separator: ", "))</div>
                </div>
                """ }.joined())
            </div>

            <div class="footer" style="text-align: center; color: #999; margin-top: 40px;">
                <p>FieldMind 乡村调研平台</p>
                <p>生成时间: \(Date().formatted(date: .long, time: .shortened))</p>
            </div>
        </body>
        </html>
        """

        return saveToFile(content: html, filename: "文创分析_\(results.keywords.joined(separator: "_"))_\(timestamp()).html")
    }

    private func exportCreativeAnalysisMarkdown(_ results: CreativeAnalysisResponse) -> URL? {
        // TODO: 实现 Markdown 导出
        return nil
    }

    private func exportCreativeAnalysisText(_ results: CreativeAnalysisResponse) -> URL? {
        // TODO: 实现文本导出
        return nil
    }

    // MARK: - 辅助方法

    private func saveToFile(content: String, filename: String) -> URL? {
        let tempDir = FileManager.default.temporaryDirectory
        let fileURL = tempDir.appendingPathComponent(filename)

        do {
            try content.write(to: fileURL, atomically: true, encoding: .utf8)
            return fileURL
        } catch {
            print("保存文件失败: \(error)")
            return nil
        }
    }

    private func timestamp() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd_HHmmss"
        return formatter.string(from: Date())
    }

    func openFile(_ url: URL) {
        NSWorkspace.shared.open(url)
    }
}

enum ExportFormat {
    case html
    case markdown
    case text
}
