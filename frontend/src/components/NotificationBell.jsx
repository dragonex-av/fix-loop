import React, { useState, useEffect } from 'react';
import { getNotifications, getUnreadCount, markNotifRead, markAllNotifsRead } from '../services/api';
import { Bell, Check, Clock, ExternalLink } from 'lucide-react';

export default function NotificationBell({ onSelectTicket }) {
  const [open, setOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);

  // Poll unread count every 10 seconds
  useEffect(() => {
    fetchCount();
    const timer = setInterval(fetchCount, 10000);
    return () => clearInterval(timer);
  }, []);

  const fetchCount = async () => {
    try {
      const res = await getUnreadCount();
      setUnreadCount(res.data.unread_count || 0);
    } catch (e) {
      // ignore silently if not logged in
    }
  };

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const res = await getNotifications(false);
      setNotifications(res.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const toggleDropdown = () => {
    if (!open) {
      loadNotifications();
    }
    setOpen(!open);
  };

  const handleNotificationClick = async (notif) => {
    if (!notif.is_read) {
      await markNotifRead(notif.id);
      setNotifications(prev => prev.map(n => n.id === notif.id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    }
    if (notif.ticket_id && onSelectTicket) {
      onSelectTicket(notif.ticket_id);
      setOpen(false);
    }
  };

  const handleMarkAll = async () => {
    await markAllNotifsRead();
    setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    setUnreadCount(0);
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={toggleDropdown}
        className="relative p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition"
        title="Notifications"
      >
        <Bell className="w-4 h-4" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-rose-500 text-white text-[9px] font-bold flex items-center justify-center animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 sm:w-96 bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl z-50 overflow-hidden text-xs text-slate-200">
          <div className="p-3 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
            <div className="flex items-center gap-2">
              <span className="font-bold text-white">Notifications</span>
              {unreadCount > 0 && (
                <span className="bg-teal-500/20 text-teal-300 text-[10px] font-bold px-1.5 py-0.2 rounded">
                  {unreadCount} new
                </span>
              )}
            </div>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAll}
                className="text-[10px] text-teal-400 hover:text-teal-300 font-semibold flex items-center gap-1"
              >
                <Check className="w-3 h-3" /> Mark all read
              </button>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto divide-y divide-slate-800">
            {loading ? (
              <div className="p-6 text-center text-slate-500">Loading...</div>
            ) : notifications.length === 0 ? (
              <div className="p-6 text-center text-slate-500">
                <Bell className="w-8 h-8 text-slate-700 mx-auto mb-2" />
                <p>No notifications yet</p>
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  onClick={() => handleNotificationClick(n)}
                  className={`p-3 hover:bg-slate-800/60 transition cursor-pointer ${
                    !n.is_read ? 'bg-slate-800/30 border-l-2 border-teal-500' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className={`font-semibold ${!n.is_read ? 'text-white' : 'text-slate-300'}`}>
                      {n.title}
                    </p>
                    <span className="text-[10px] text-slate-500 whitespace-nowrap">
                      {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p className="text-slate-400 mt-1 leading-relaxed text-[11px]">{n.body}</p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
