import Foundation

/// API 端点定义
enum APIEndpoint {
    // Dashboard
    case dashboard(projectId: String)
    case quickStats(projectId: String)

    // Business Analysis
    case businessAnalysis(projectId: String)
    case existingFormats(projectId: String)
    case businessSynergy(projectId: String)

    // Aggregate
    case topicDistribution(projectId: String)
    case topEntities(projectId: String)
    case wordCountStats(projectId: String)
    case timelineDistribution(projectId: String)
    case generateReport(projectId: String)

    // Chat
    case chatQuery
    case availableDocuments(projectId: String)
    case projectAsk(projectId: String)
    case projectContext(projectId: String)
    case projectConversations(projectId: String)

    // Chat Sessions
    case createSession
    case getSession(sessionId: String)
    case projectSessions(projectId: String)
    case sendMessage(sessionId: String)
    case getMessages(sessionId: String)
    case deleteSession(sessionId: String)
    case evolveSkill(sessionId: String)

    // Document Processing
    case documentStatus(documentId: String)
    case reprocessDocument(documentId: String)
    case chunksPreview(documentId: String)
    case chunksStatistics(projectId: String)
    case semanticSearch(projectId: String)

    // Batch Processing
    case batchProcess
    case batchStatus
    case reprocessFailed
    case processProject

    // Knowledge Graph
    case objectLineage(fid: String)
    case objectDetails(fid: String)
    case projectObjects(projectId: String)
    case discoverRelations
    case discoverAllRelations(projectId: String)
    case objectRelations(fid: String)
    case objectRecommend(fid: String)
    case hotConnections(projectId: String)

    // Timeline
    case alignTimestamps(documentId: String)
    case contentAtTime(documentId: String)
    case entityTimeline(entityName: String)
    case entityProfile(entityName: String)
    case eventProfile(eventSummary: String)
    case timestampValidation(documentId: String)

    // Creative Analysis
    case creativeAnalysis(projectId: String)
    case culturalElements(projectId: String)

    // Search
    case searchWithCitation

    // Custom endpoint for flexible API calls
    case custom(String, queryItems: [URLQueryItem] = [])

    var path: String {
        switch self {
        // Dashboard
        case .dashboard(let projectId):
            return "/dashboard/\(projectId)"
        case .quickStats(let projectId):
            return "/quick-stats/\(projectId)"

        // Business Analysis
        case .businessAnalysis(let projectId):
            return "/projects/\(projectId)/analyze"
        case .existingFormats(let projectId):
            return "/projects/\(projectId)/formats/existing"
        case .businessSynergy(let projectId):
            return "/projects/\(projectId)/synergy"

        // Aggregate
        case .topicDistribution(let projectId):
            return "/projects/\(projectId)/topic-distribution"
        case .topEntities(let projectId):
            return "/projects/\(projectId)/top-entities"
        case .wordCountStats(let projectId):
            return "/projects/\(projectId)/word-count-stats"
        case .timelineDistribution(let projectId):
            return "/projects/\(projectId)/timeline-distribution"
        case .generateReport(let projectId):
            return "/projects/\(projectId)/generate-report"

        // Chat
        case .chatQuery:
            return "/query"
        case .availableDocuments(let projectId):
            return "/available-documents/\(projectId)"
        case .projectAsk(let projectId):
            return "/projects/\(projectId)/ask"
        case .projectContext(let projectId):
            return "/projects/\(projectId)/context"
        case .projectConversations(let projectId):
            return "/projects/\(projectId)/conversations"

        // Chat Sessions
        case .createSession:
            return "/sessions"
        case .getSession(let sessionId):
            return "/sessions/\(sessionId)"
        case .projectSessions(let projectId):
            return "/projects/\(projectId)/sessions"
        case .sendMessage(let sessionId):
            return "/sessions/\(sessionId)/messages"
        case .getMessages(let sessionId):
            return "/sessions/\(sessionId)/messages"
        case .deleteSession(let sessionId):
            return "/sessions/\(sessionId)"
        case .evolveSkill(let sessionId):
            return "/sessions/\(sessionId)/evolve-skill"

        // Document Processing
        case .documentStatus(let documentId):
            return "/documents/\(documentId)/status"
        case .reprocessDocument(let documentId):
            return "/documents/\(documentId)/reprocess"
        case .chunksPreview(let documentId):
            return "/documents/\(documentId)/chunks/preview"
        case .chunksStatistics(let projectId):
            return "/projects/\(projectId)/chunks/statistics"
        case .semanticSearch(let projectId):
            return "/projects/\(projectId)/semantic-search"

        // Batch Processing
        case .batchProcess:
            return "/process"
        case .batchStatus:
            return "/status"
        case .reprocessFailed:
            return "/reprocess-failed"
        case .processProject:
            return "/process-project"

        // Knowledge Graph
        case .objectLineage(let fid):
            return "/objects/\(fid)/lineage"
        case .objectDetails(let fid):
            return "/objects/\(fid)"
        case .projectObjects(let projectId):
            return "/projects/\(projectId)/objects"
        case .discoverRelations:
            return "/relations/discover"
        case .discoverAllRelations(let projectId):
            return "/projects/\(projectId)/relations/discover-all"
        case .objectRelations(let fid):
            return "/objects/\(fid)/relations"
        case .objectRecommend(let fid):
            return "/objects/\(fid)/recommend"
        case .hotConnections(let projectId):
            return "/projects/\(projectId)/hot-connections"

        // Timeline
        case .alignTimestamps(let documentId):
            return "/documents/\(documentId)/align-timestamps"
        case .contentAtTime(let documentId):
            return "/documents/\(documentId)/content-at-time"
        case .entityTimeline(let entityName):
            return "/entities/\(entityName)/timeline"
        case .entityProfile(let entityName):
            return "/entities/\(entityName)/profile"
        case .eventProfile(let eventSummary):
            return "/events/\(eventSummary)/profile"
        case .timestampValidation(let documentId):
            return "/documents/\(documentId)/timestamp-validation"

        // Creative Analysis
        case .creativeAnalysis(let projectId):
            return "/projects/\(projectId)/analyze"
        case .culturalElements(let projectId):
            return "/projects/\(projectId)/cultural-elements"

        // Search
        case .searchWithCitation:
            return "/search-with-citation"

        // Custom
        case .custom(let path, _):
            return path
        }
    }

    var queryItems: [URLQueryItem] {
        switch self {
        case .custom(_, let items):
            return items
        default:
            return []
        }
    }

    func with(queryItem name: String, value: String) -> APIEndpoint {
        switch self {
        case .custom(let path, let existingItems):
            let newItem = URLQueryItem(name: name, value: value)
            return .custom(path, queryItems: existingItems + [newItem])
        default:
            let newItem = URLQueryItem(name: name, value: value)
            return .custom(self.path, queryItems: [newItem])
        }
    }
}
