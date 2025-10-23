/**
 * Chat System Type Definitions
 * Types for real-time chat functionality
 */

export type RoomType = 'DIRECT' | 'GROUP' | 'AI_BOT' | 'CHANNEL';
export type MessageStatus =
  | 'PENDING'
  | 'SENT'
  | 'DELIVERED'
  | 'READ'
  | 'FAILED';

export interface ChatUser {
  id: string;
  email: string;
  avatarImage?: {
    id: string;
    imageUrl: string;
  } | null;
  isOnline?: boolean;
  lastSeen?: string;
}

export interface ChatRoom {
  id: string;
  roomType: RoomType;
  name?: string;
  description?: string;
  avatarImage?: {
    id: string;
    imageUrl: string;
  } | null;
  isGroup: boolean;
  lastMessage?: ChatMessage;
  lastMessageAt?: string;
  unreadCount: number;
  members: ChatRoomMember[];
  createdAt: string;
  updatedAt: string;
}

export interface ChatMessage {
  id: string;
  roomId: string;
  sender: ChatUser;
  content: string;
  messageType: 'TEXT' | 'IMAGE' | 'FILE' | 'SYSTEM';
  replyTo?: string;
  mentions?: string[];
  status: MessageStatus;
  isEdited: boolean;
  readBy: string[];
  createdAt: string;
  updatedAt: string;
}

export interface ChatRoomMember {
  id: string;
  user: ChatUser;
  role: 'OWNER' | 'ADMIN' | 'MEMBER';
  unreadCount: number;
  lastReadAt?: string;
  joinedAt: string;
}

export interface TypingIndicator {
  roomId: string;
  userId: string;
  email: string;
}

export interface SendMessagePayload {
  roomId: string;
  content: string;
  messageType?: 'TEXT' | 'IMAGE' | 'FILE';
  replyTo?: string;
  mentions?: string[];
}
