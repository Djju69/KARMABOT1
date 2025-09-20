"""
Утилита для отправки email отчётов
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Tuple, Optional
import os

logger = logging.getLogger(__name__)


class EmailSender:
    """Класс для отправки email"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@karma-system.com")
    
    async def send_email(self, to_email: str, subject: str, text: str, 
                        attachments: List[Tuple[str, bytes, str]] = None) -> bool:
        """
        Отправляет email с вложениями
        
        Args:
            to_email: Email получателя
            subject: Тема письма
            text: Текст письма
            attachments: Список вложений [(filename, content_bytes, mime_type), ...]
        
        Returns:
            bool: True если отправлено успешно
        """
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured")
                return False
            
            # Создаем сообщение
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = f"[KarmaSystem] {subject}"
            
            # Добавляем текст
            msg.attach(MIMEText(text, 'plain', 'utf-8'))
            
            # Добавляем вложения
            if attachments:
                for filename, content, mime_type in attachments:
                    attachment = MIMEBase(*mime_type.split('/'))
                    attachment.set_payload(content)
                    encoders.encode_base64(attachment)
                    attachment.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}'
                    )
                    msg.attach(attachment)
            
            # Подключаемся к SMTP серверу
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            # Отправляем
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    async def send_report_email(self, to_email: str, report_data: dict, 
                               period: str, role: str) -> bool:
        """
        Отправляет отчёт по email
        
        Args:
            to_email: Email получателя
            report_data: Данные отчёта
            period: Период отчёта
            role: Роль пользователя
        
        Returns:
            bool: True если отправлено успешно
        """
        try:
            subject = f"Отчёт {role} за {period}"
            
            # Формируем текст письма
            text = f"""
Здравствуйте!

Прикрепляем запрошенный отчёт за период: {period}

Роль: {role}
Дата создания: {report_data.get('created_at', 'Неизвестно')}

---
С уважением,
Команда Karma System
            """
            
            # В реальной реализации здесь будет генерация PDF/CSV
            attachments = []
            
            return await self.send_email(to_email, subject, text, attachments)
            
        except Exception as e:
            logger.error(f"Error sending report email: {e}")
            return False
