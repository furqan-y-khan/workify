from datetime import datetime, timedelta
from utils.database import get_db
from utils.location_manager import calculate_distance

class AnalyticsManager:
    @staticmethod
    def calculate_user_metrics(user_id):
        """Calculate and store user metrics"""
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            now = datetime.now()
            period_start = (now - timedelta(days=30)).isoformat()
            period_end = now.isoformat()
            
            # Calculate application success rate
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_applications,
                    SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) as accepted_applications
                FROM applications
                WHERE applicant_id = ?
                AND created_at BETWEEN ? AND ?
            """, (user_id, period_start, period_end))
            
            app_stats = cursor.fetchone()
            if app_stats['total_applications'] > 0:
                success_rate = (app_stats['accepted_applications'] / app_stats['total_applications']) * 100
                
                cursor.execute("""
                    INSERT INTO user_analytics 
                    (user_id, metric_name, metric_value, period_start, period_end, created_at)
                    VALUES (?, 'application_success_rate', ?, ?, ?, ?)
                """, (user_id, success_rate, period_start, period_end, now.isoformat()))
            
            # Calculate average response time
            cursor.execute("""
                SELECT AVG(response_time) as avg_response_time
                FROM applications
                WHERE job_poster_id = ?
                AND created_at BETWEEN ? AND ?
                AND response_time IS NOT NULL
            """, (user_id, period_start, period_end))
            
            response_stats = cursor.fetchone()
            if response_stats['avg_response_time']:
                cursor.execute("""
                    INSERT INTO user_analytics 
                    (user_id, metric_name, metric_value, period_start, period_end, created_at)
                    VALUES (?, 'avg_response_time', ?, ?, ?, ?)
                """, (user_id, response_stats['avg_response_time'], 
                     period_start, period_end, now.isoformat()))
            
            # Calculate popular job categories
            cursor.execute("""
                SELECT trade_category, COUNT(*) as category_count
                FROM jobs
                WHERE created_at BETWEEN ? AND ?
                AND status = 'Open'
                GROUP BY trade_category
                ORDER BY category_count DESC
                LIMIT 5
            """, (period_start, period_end))
            
            categories = cursor.fetchall()
            for idx, cat in enumerate(categories):
                cursor.execute("""
                    INSERT INTO user_analytics 
                    (user_id, metric_name, metric_value, period_start, period_end, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, f"popular_category_{idx+1}", cat['category_count'],
                     period_start, period_end, now.isoformat()))
            
            conn.commit()
            
        finally:
            conn.close()
    
    @staticmethod
    def get_job_recommendations(user_id):
        """Get personalized job recommendations for a user"""
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # Get user preferences and history
            cursor.execute("""
                SELECT u.*, 
                       GROUP_CONCAT(DISTINCT c.name) as certifications,
                       GROUP_CONCAT(DISTINCT wh.trade_category) as experience_categories
                FROM users u
                LEFT JOIN certifications c ON u.user_id = c.user_id
                LEFT JOIN work_history wh ON u.user_id = wh.user_id
                WHERE u.user_id = ?
                GROUP BY u.user_id
            """, (user_id,))
            
            user = cursor.fetchone()
            if not user:
                return []
            
            # Build recommendation query
            query = """
                SELECT j.*, u.company_name, u.name as poster_name,
                       COUNT(DISTINCT a.application_id) as application_count
                FROM jobs j
                JOIN users u ON j.job_poster_id = u.user_id
                LEFT JOIN applications a ON j.job_id = a.job_id
                WHERE j.status = 'Open'
                AND (SELECT COUNT(*) FROM applications WHERE job_id = j.job_id) < j.workers_needed
            """
            params = []
            
            # Match trade categories from experience
            if user['experience_categories']:
                categories = user['experience_categories'].split(",")
                placeholders = ",".join("?" * len(categories))
                query += f" AND j.trade_category IN ({placeholders})"
                params.extend(categories)
            
            # Match required certifications
            if user['certifications']:
                query += " AND j.requirements LIKE ?"
                params.append(f"%{user['certifications']}%")
            
            # Group and order
            query += """ 
                GROUP BY j.job_id
                ORDER BY j.created_at DESC
                LIMIT 10
            """
            
            cursor.execute(query, params)
            jobs = cursor.fetchall()
            
            # Calculate match scores and sort
            scored_jobs = []
            for job in jobs:
                score = 0
                
                # Location score
                if user['latitude'] and user['longitude'] and job['latitude'] and job['longitude']:
                    distance = calculate_distance(
                        user['latitude'], user['longitude'],
                        job['latitude'], job['longitude']
                    )
                    score += max(0, 100 - distance)  # Higher score for closer jobs
                
                # Experience match score
                if user['experience_categories'] and job['trade_category'] in user['experience_categories']:
                    score += 50
                
                # Certification match score
                if user['certifications'] and job['requirements']:
                    user_certs = set(user['certifications'].split(','))
                    required_certs = set(cert.strip() for cert in job['requirements'].split(','))
                    matching_certs = user_certs.intersection(required_certs)
                    score += len(matching_certs) * 25
                
                # Payment score
                if job['payment_amount']:
                    score += min(50, job['payment_amount'] / 100)
                
                job['match_score'] = score
                scored_jobs.append(job)
            
            # Sort by match score
            scored_jobs.sort(key=lambda x: x['match_score'], reverse=True)
            return scored_jobs
            
        finally:
            conn.close()
    
    @staticmethod
    def get_analytics_dashboard(user_id):
        """Get analytics dashboard data for premium users"""
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            now = datetime.now()
            period_start = (now - timedelta(days=30)).isoformat()
            
            dashboard = {
                'application_stats': {},
                'response_metrics': {},
                'popular_categories': [],
                'success_rate_trend': []
            }
            
            # Get latest application stats
            cursor.execute("""
                SELECT metric_name, metric_value
                FROM user_analytics
                WHERE user_id = ?
                AND metric_name = 'application_success_rate'
                AND created_at > ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id, period_start))
            
            success_rate = cursor.fetchone()
            if success_rate:
                dashboard['application_stats']['success_rate'] = success_rate['metric_value']
            
            # Get response time metrics
            cursor.execute("""
                SELECT metric_name, metric_value
                FROM user_analytics
                WHERE user_id = ?
                AND metric_name = 'avg_response_time'
                AND created_at > ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id, period_start))
            
            response_time = cursor.fetchone()
            if response_time:
                dashboard['response_metrics']['avg_response_time'] = response_time['metric_value']
            
            # Get popular categories
            cursor.execute("""
                SELECT metric_name, metric_value
                FROM user_analytics
                WHERE user_id = ?
                AND metric_name LIKE 'popular_category_%'
                AND created_at > ?
                ORDER BY metric_value DESC
            """, (user_id, period_start))
            
            categories = cursor.fetchall()
            dashboard['popular_categories'] = [
                {'category': cat['metric_name'].replace('popular_category_', ''),
                 'count': cat['metric_value']}
                for cat in categories
            ]
            
            # Get success rate trend
            cursor.execute("""
                SELECT metric_value, period_start
                FROM user_analytics
                WHERE user_id = ?
                AND metric_name = 'application_success_rate'
                AND created_at > ?
                ORDER BY period_start ASC
            """, (user_id, period_start))
            
            trend = cursor.fetchall()
            dashboard['success_rate_trend'] = [
                {'date': t['period_start'], 'rate': t['metric_value']}
                for t in trend
            ]
            
            return dashboard
            
        finally:
            conn.close() 