import { create } from 'zustand';
import type { Conversation, Message } from '../types';
import { conversationsApi } from '../services/api';

interface ConversationState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  loading: boolean;
  streaming: boolean;
  error: string | null;

  // Actions
  fetchConversations: (projectId: string) => Promise<void>;
  selectConversation: (conversationId: string) => Promise<void>;
  createConversation: (projectId: string, title?: string) => Promise<void>;
  deleteConversation: (conversationId: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  addMessage: (message: Message) => void;
  appendToLastMessage: (content: string) => void;
  clearMessages: () => void;
}

export const useConversationStore = create<ConversationState>((set, get) => ({
  conversations: [],
  currentConversation: null,
  messages: [],
  loading: false,
  streaming: false,
  error: null,

  fetchConversations: async (projectId: string) => {
    set({ loading: true, error: null });
    try {
      const response = await conversationsApi.getAll(projectId);
      set({ conversations: response.data, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  selectConversation: async (conversationId: string) => {
    set({ loading: true, error: null });
    try {
      const [convRes, messagesRes] = await Promise.all([
        conversationsApi.getById(conversationId),
        conversationsApi.getMessages(conversationId),
      ]);
      set({
        currentConversation: convRes.data,
        messages: messagesRes.data,
        loading: false,
      });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  createConversation: async (projectId: string, title?: string) => {
    set({ loading: true, error: null });
    try {
      const response = await conversationsApi.create(projectId, title);
      set({ loading: false });
      await get().fetchConversations(projectId);
      await get().selectConversation(response.data.id);
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  deleteConversation: async (conversationId: string) => {
    set({ loading: true, error: null });
    try {
      await conversationsApi.delete(conversationId);
      set({
        currentConversation: null,
        messages: [],
        loading: false,
      });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  sendMessage: async (content: string) => {
    const conversation = get().currentConversation;
    if (!conversation) return;

    // Add user message immediately
    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: conversation.id,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    get().addMessage(userMessage);

    set({ streaming: true, error: null });

    try {
      const eventSource = new EventSource(
        conversationsApi.sendMessage(conversation.id, content) +
          `?message=${encodeURIComponent(content)}`
      );

      let assistantMessageId = '';
      let assistantContent = '';

      eventSource.addEventListener('text', (e) => {
        const data = JSON.parse(e.data);
        assistantContent += data.content;
        get().appendToLastMessage(data.content);
      });

      eventSource.addEventListener('tool_start', (e) => {
        const data = JSON.parse(e.data);
        assistantContent += `\n[🔧 ${data.tool_name}]\n`;
        get().appendToLastMessage(`\n[🔧 ${data.tool_name}]\n`);
      });

      eventSource.addEventListener('tool_result', (e) => {
        const data = JSON.parse(e.data);
        assistantContent += `\n[✓ ${data.tool_name} 完成]\n`;
        get().appendToLastMessage(`\n[✓ ${data.tool_name} 完成]\n`);
      });

      eventSource.addEventListener('citation', (e) => {
        const data = JSON.parse(e.data);
        assistantContent += `[${data.citation_id}]`;
        get().appendToLastMessage(`[${data.citation_id}]`);
      });

      eventSource.addEventListener('done', (e) => {
        const data = JSON.parse(e.data);
        assistantMessageId = data.message_id;
        eventSource.close();
        set({ streaming: false });

        // Update the last message with proper ID
        const messages = get().messages;
        const lastMessage = messages[messages.length - 1];
        if (lastMessage && lastMessage.role === 'assistant') {
          lastMessage.id = assistantMessageId;
          set({ messages: [...messages] });
        }
      });

      eventSource.addEventListener('error', (e: any) => {
        console.error('SSE Error:', e);
        eventSource.close();
        set({ streaming: false, error: 'Stream connection error' });
      });

      // Initialize assistant message
      const assistantMessage: Message = {
        id: `temp-assistant-${Date.now()}`,
        conversation_id: conversation.id,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
      };
      get().addMessage(assistantMessage);
    } catch (error: any) {
      set({ streaming: false, error: error.message });
    }
  },

  addMessage: (message: Message) => {
    set((state) => ({ messages: [...state.messages, message] }));
  },

  appendToLastMessage: (content: string) => {
    set((state) => {
      const messages = [...state.messages];
      const lastMessage = messages[messages.length - 1];
      if (lastMessage && lastMessage.role === 'assistant') {
        lastMessage.content += content;
      }
      return { messages };
    });
  },

  clearMessages: () => {
    set({ messages: [], currentConversation: null });
  },
}));
