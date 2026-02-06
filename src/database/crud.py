"""
CRUD操作
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from src.database.models import (
    User, Content, ContentSchedule, Conversation, Message,
    UserInteraction, AnalyticsSnapshot, AgentWorkflow, FAQ,
    LifecycleStage, RFMSegment
)


class UserCRUD:
    """用户CRUD操作"""

    @staticmethod
    def create_user(db: Session, openid: str, **kwargs) -> User:
        """创建新用户"""
        user = User(openid=openid, **kwargs)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user_by_openid(db: Session, openid: str) -> Optional[User]:
        """根据OpenID获取用户"""
        return db.query(User).filter(User.openid == openid).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
        """更新用户信息"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def get_active_users(db: Session, days: int = 7, limit: int = 100) -> List[User]:
        """获取活跃用户"""
        since = datetime.utcnow() - timedelta(days=days)
        return db.query(User).filter(
            and_(
                User.is_subscribed == True,
                User.last_interaction_time >= since
            )
        ).order_by(User.last_interaction_time.desc()).limit(limit).all()

    @staticmethod
    def get_dormant_users(db: Session, days: int = 30) -> List[User]:
        """获取沉睡用户"""
        since = datetime.utcnow() - timedelta(days=days)
        return db.query(User).filter(
            and_(
                User.is_subscribed == True,
                or_(
                    User.last_interaction_time < since,
                    User.last_interaction_time.is_(None)
                )
            )
        ).all()


class ContentCRUD:
    """内容CRUD操作"""

    @staticmethod
    def create_content(db: Session, **kwargs) -> Content:
        """创建内容"""
        content = Content(**kwargs)
        db.add(content)
        db.commit()
        db.refresh(content)
        return content

    @staticmethod
    def get_content_by_id(db: Session, content_id: int) -> Optional[Content]:
        """根据ID获取内容"""
        return db.query(Content).filter(Content.id == content_id).first()

    @staticmethod
    def get_content_by_status(db: Session, status: str, limit: int = 50) -> List[Content]:
        """根据状态获取内容"""
        return db.query(Content).filter(
            Content.status == status
        ).order_by(Content.created_at.desc()).limit(limit).all()

    @staticmethod
    def update_content(db: Session, content_id: int, **kwargs) -> Optional[Content]:
        """更新内容"""
        content = db.query(Content).filter(Content.id == content_id).first()
        if content:
            for key, value in kwargs.items():
                setattr(content, key, value)
            content.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(content)
        return content

    @staticmethod
    def get_top_content(db: Session, days: int = 7, limit: int = 10) -> List[Content]:
        """获取热门内容"""
        since = datetime.utcnow() - timedelta(days=days)
        return db.query(Content).filter(
            and_(
                Content.status == "published",
                Content.publish_time >= since
            )
        ).order_by(Content.views.desc()).limit(limit).all()

    @staticmethod
    def schedule_content(db: Session, content_id: int, scheduled_time: datetime) -> ContentSchedule:
        """调度内容发布"""
        schedule = ContentSchedule(
            content_id=content_id,
            scheduled_time=scheduled_time
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        return schedule

    @staticmethod
    def get_pending_schedules(db: Session, before_time: datetime) -> List[ContentSchedule]:
        """获取待发布的调度任务"""
        return db.query(ContentSchedule).filter(
            and_(
                ContentSchedule.status == "pending",
                ContentSchedule.scheduled_time <= before_time
            )
        ).order_by(ContentSchedule.scheduled_time).all()


class ConversationCRUD:
    """会话CRUD操作"""

    @staticmethod
    def create_conversation(db: Session, user_id: int, **kwargs) -> Conversation:
        """创建会话"""
        conversation = Conversation(user_id=user_id, **kwargs)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def get_active_conversation(db: Session, user_id: int) -> Optional[Conversation]:
        """获取用户的活跃会话"""
        return db.query(Conversation).filter(
            and_(
                Conversation.user_id == user_id,
                Conversation.status == "active"
            )
        ).order_by(Conversation.created_at.desc()).first()

    @staticmethod
    def add_message(db: Session, conversation_id: int, user_id: int,
                   role: str, content: str, **kwargs) -> Message:
        """添加消息"""
        message = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=content,
            **kwargs
        )
        db.add(message)

        # 更新会话的最后消息时间
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        if conversation:
            conversation.last_message_time = datetime.utcnow()
            conversation.message_count += 1

        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def get_conversation_history(db: Session, conversation_id: int,
                                 limit: int = 50) -> List[Message]:
        """获取会话历史"""
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).limit(limit).all()

    @staticmethod
    def get_recent_messages(db: Session, user_id: int,
                           hours: int = 24, limit: int = 20) -> List[Message]:
        """获取用户最近的对话历史"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return db.query(Message).filter(
            and_(
                Message.user_id == user_id,
                Message.created_at >= since
            )
        ).order_by(Message.created_at.desc()).limit(limit).all()


class AnalyticsCRUD:
    """分析数据CRUD操作"""

    @staticmethod
    def create_snapshot(db: Session, snapshot_date: datetime,
                       snapshot_type: str, **kwargs) -> AnalyticsSnapshot:
        """创建数据快照"""
        snapshot = AnalyticsSnapshot(
            snapshot_date=snapshot_date,
            snapshot_type=snapshot_type,
            **kwargs
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    @staticmethod
    def get_latest_snapshot(db: Session, snapshot_type: str) -> Optional[AnalyticsSnapshot]:
        """获取最新的快照"""
        return db.query(AnalyticsSnapshot).filter(
            AnalyticsSnapshot.snapshot_type == snapshot_type
        ).order_by(AnalyticsSnapshot.snapshot_date.desc()).first()

    @staticmethod
    def record_interaction(db: Session, user_id: int, interaction_type: str,
                          content_id: Optional[int] = None, **kwargs) -> UserInteraction:
        """记录用户互动"""
        interaction = UserInteraction(
            user_id=user_id,
            interaction_type=interaction_type,
            content_id=content_id,
            **kwargs
        )
        db.add(interaction)

        # 更新用户的互动统计
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.total_interactions += 1
            user.last_interaction_time = datetime.utcnow()

        db.commit()
        db.refresh(interaction)
        return interaction

    @staticmethod
    def get_user_interaction_stats(db: Session, user_id: int,
                                   days: int = 30) -> Dict[str, int]:
        """获取用户互动统计"""
        since = datetime.utcnow() - timedelta(days=days)

        interactions = db.query(
            UserInteraction.interaction_type,
            func.count(UserInteraction.id)
        ).filter(
            and_(
                UserInteraction.user_id == user_id,
                UserInteraction.created_at >= since
            )
        ).group_by(UserInteraction.interaction_type).all()

        return {itype: count for itype, count in interactions}


class AgentWorkflowCRUD:
    """Agent工作流CRUD操作"""

    @staticmethod
    def create_workflow(db: Session, workflow_id: str, agent_type: str,
                       input_data: Dict[str, Any]) -> AgentWorkflow:
        """创建工作流记录"""
        workflow = AgentWorkflow(
            workflow_id=workflow_id,
            agent_type=agent_type,
            input_data=input_data
        )
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        return workflow

    @staticmethod
    def update_workflow(db: Session, workflow_id: str, **kwargs) -> Optional[AgentWorkflow]:
        """更新工作流"""
        workflow = db.query(AgentWorkflow).filter(
            AgentWorkflow.workflow_id == workflow_id
        ).first()
        if workflow:
            for key, value in kwargs.items():
                setattr(workflow, key, value)
            if kwargs.get("status") == "completed":
                workflow.completed_at = datetime.utcnow()
                if workflow.started_at:
                    workflow.duration_ms = int(
                        (workflow.completed_at - workflow.started_at).total_seconds() * 1000
                    )
            db.commit()
            db.refresh(workflow)
        return workflow

    @staticmethod
    def get_workflow_stats(db: Session, agent_type: Optional[str] = None,
                          days: int = 7) -> Dict[str, Any]:
        """获取工作流统计"""
        since = datetime.utcnow() - timedelta(days=days)

        query = db.query(AgentWorkflow).filter(
            AgentWorkflow.started_at >= since
        )

        if agent_type:
            query = query.filter(AgentWorkflow.agent_type == agent_type)

        total = query.count()
        completed = query.filter(AgentWorkflow.status == "completed").count()
        failed = query.filter(AgentWorkflow.status == "failed").count()

        # 计算平均执行时间
        avg_duration = db.query(func.avg(AgentWorkflow.duration_ms)).filter(
            and_(
                AgentWorkflow.started_at >= since,
                AgentWorkflow.status == "completed"
            )
        ).scalar()

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "success_rate": completed / total if total > 0 else 0,
            "avg_duration_ms": float(avg_duration) if avg_duration else 0
        }


class FAQCRUD:
    """FAQ CRUD操作"""

    @staticmethod
    def create_faq(db: Session, question: str, answer: str, **kwargs) -> FAQ:
        """创建FAQ"""
        faq = FAQ(question=question, answer=answer, **kwargs)
        db.add(faq)
        db.commit()
        db.refresh(faq)
        return faq

    @staticmethod
    def search_faq(db: Session, query: str, category: Optional[str] = None,
                  limit: int = 5) -> List[FAQ]:
        """搜索FAQ"""
        query_filter = and_(
            FAQ.is_active == True,
            or_(
                FAQ.question.ilike(f"%{query}%"),
                FAQ.keywords.contains([query])
            )
        )

        if category:
            query_filter = and_(query_filter, FAQ.category == category)

        return db.query(FAQ).filter(query_filter).order_by(
            FAQ.priority.desc(),
            FAQ.effectiveness_score.desc()
        ).limit(limit).all()

    @staticmethod
    def update_faq_hit(db: Session, faq_id: int) -> Optional[FAQ]:
        """更新FAQ命中次数"""
        faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
        if faq:
            faq.hit_count += 1
            faq.last_hit_time = datetime.utcnow()
            db.commit()
            db.refresh(faq)
        return faq
