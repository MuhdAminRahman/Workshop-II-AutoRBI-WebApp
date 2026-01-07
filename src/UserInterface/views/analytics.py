"""Analytics Dashboard - RBI Risk Assessment Focus (Improved UI)."""

from typing import Optional, Dict, Any, List
import customtkinter as ctk
from AutoRBI_Database.database.session import SessionLocal
from AutoRBI_Database.database.models.equipment import Equipment as DBEquipment
from AutoRBI_Database.database.models.component import Component as DBComponent
from AutoRBI_Database.database.models.correction_log import CorrectionLog
from AutoRBI_Database.database.models.work_history import WorkHistory
from AutoRBI_Database.database.models.users import User
from AutoRBI_Database.database.models.work import Work
from AutoRBI_Database.database.models.assign_work import AssignWork
from sqlalchemy import func


class RBIAnalyticsEngine:
    """Backend: Calculate RBI-relevant metrics from database."""
    
    @staticmethod
    def get_user_works(db, user_id: int) -> List[Dict]:
        """Get all works assigned to a user."""
        works = db.query(Work).join(
            AssignWork, Work.work_id == AssignWork.work_id
        ).filter(
            AssignWork.user_id == user_id
        ).order_by(Work.created_at.desc()).all()
        
        return [
            {
                'work_id': work.work_id,
                'work_name': work.work_name,
                'status': work.status,
                'created_at': work.created_at,
                'description': work.description or ""
            }
            for work in works
        ]
    
    @staticmethod
    def get_work_health_score(db, work_id: int) -> Dict:
        """Health score for RBI data readiness."""
        total_eq = db.query(DBEquipment).filter(
            DBEquipment.work_id == work_id
        ).count()
        
        extracted_eq = db.query(DBEquipment).filter(
            DBEquipment.work_id == work_id,
            DBEquipment.extracted_date.isnot(None)
        ).count()
        
        extraction_rate = (extracted_eq / total_eq * 100) if total_eq > 0 else 0
        
        # Critical RBI fields
        critical_fields = ['fluid', 'material_spec', 'design_temp', 'design_pressure']
        
        all_components = db.query(DBComponent).join(DBEquipment).filter(
            DBEquipment.work_id == work_id
        ).all()
        
        if not all_components:
            return {
                'health_score': 0,
                'extraction_rate': 0,
                'completeness_rate': 0,
                'risk_level': 'UNKNOWN',
                'status_color': ('gray50', 'gray70'),
            }
        
        filled_critical = sum(
            1 for comp in all_components
            for field in critical_fields
            if getattr(comp, field)
        )
        
        total_critical = len(all_components) * len(critical_fields)
        completeness_rate = (filled_critical / total_critical * 100) if total_critical > 0 else 0
        
        # Get correction count
        correction_count = db.query(CorrectionLog).join(DBEquipment).filter(
            DBEquipment.work_id == work_id
        ).count()
        
        # Health score: 40% extraction + 40% completeness + 20% quality
        correction_penalty = min(20, correction_count * 2)
        health_score = (
            (extraction_rate * 0.4) +
            (completeness_rate * 0.4) +
            (20 - correction_penalty)
        )
        
        # Color & risk
        if health_score >= 85:
            risk = 'LOW - Ready'
            color = ('#2ecc71', '#27ae60')
        elif health_score >= 70:
            risk = 'MEDIUM - Review'
            color = ('#f39c12', '#e67e22')
        elif health_score >= 50:
            risk = 'HIGH - Gaps'
            color = ('#e74c3c', '#c0392b')
        else:
            risk = 'CRITICAL'
            color = ('#c0392b', '#8b0000')
        
        return {
            'health_score': round(health_score, 1),
            'extraction_rate': round(extraction_rate, 1),
            'completeness_rate': round(completeness_rate, 1),
            'risk_level': risk,
            'status_color': color,
            'total_equipment': total_eq,
            'extracted_equipment': extracted_eq,
        }
    
    @staticmethod
    def get_critical_gaps(db, work_id: int) -> List[Dict]:
        """Fields missing for RBI assessment."""
        critical_fields = {
            'fluid': 'Fluid Type',
            'material_spec': 'Material Spec',
            'design_temp': 'Design Temp',
            'design_pressure': 'Design Pressure',
        }
        
        gaps = []
        for field, label in critical_fields.items():
            missing = db.query(DBComponent).join(DBEquipment).filter(
                DBEquipment.work_id == work_id,
                getattr(DBComponent, field) == None
            ).count()
            
            if missing > 0:
                gaps.append({
                    'field': label,
                    'missing_count': missing,
                    'severity': 'HIGH' if missing > 5 else 'MEDIUM'
                })
        
        return sorted(gaps, key=lambda x: x['missing_count'], reverse=True)
    
    @staticmethod
    def get_equipment_status(db, work_id: int) -> List[Dict]:
        """Equipment prioritized by completeness."""
        critical_fields = ['fluid', 'material_spec', 'design_temp', 'design_pressure']
        
        equipment_list = db.query(DBEquipment).filter(
            DBEquipment.work_id == work_id
        ).all()
        
        ranking = []
        for eq in equipment_list:
            components = db.query(DBComponent).filter(
                DBComponent.equipment_id == eq.equipment_id
            ).all()
            
            total_fields = len(components) * len(critical_fields)
            filled = sum(
                1 for c in components
                for f in critical_fields
                if getattr(c, f)
            )
            
            completeness = (filled / total_fields * 100) if total_fields > 0 else 0
            
            if completeness >= 90:
                status = '✓'
                color = '#2ecc71'
            elif completeness >= 70:
                status = '⚠'
                color = '#f39c12'
            else:
                status = '✗'
                color = '#e74c3c'
            
            ranking.append({
                'equipment_no': eq.equipment_no,
                'completeness': round(completeness, 1),
                'status': status,
                'color': color,
                'components': len(components),
            })
        
        return sorted(ranking, key=lambda x: x['completeness'])
    
    @staticmethod
    def get_team_stats(db, work_id: int) -> Dict:
        """Extraction and correction activity."""
        extract_count = db.query(WorkHistory).filter(
            WorkHistory.work_id == work_id,
            WorkHistory.action_type == 'extract'
        ).count()
        
        correct_count = db.query(WorkHistory).filter(
            WorkHistory.work_id == work_id,
            WorkHistory.action_type.in_(['correct', 'generate_excel'])
        ).count()
        
        total_corrections = db.query(CorrectionLog).join(DBEquipment).filter(
            DBEquipment.work_id == work_id
        ).count()
        
        return {
            'extraction_actions': extract_count,
            'correction_actions': correct_count,
            'total_corrections': total_corrections,
        }


class AnalyticsView:
    """RBI Analytics Dashboard - Improved CTK UI."""
    
    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self.current_work_id = None
        self.user_works = []
        self.selected_work_var = ctk.StringVar(value="Select Work")
    
    def _load_user_works(self):
        """Load all works assigned to the current user."""
        db = SessionLocal()
        try:
            user_id = self.controller.current_user.get("id")
            if user_id:
                engine = RBIAnalyticsEngine()
                self.user_works = engine.get_user_works(db, user_id)
                
                if hasattr(self, 'work_dropdown'):
                    work_names = ["Select Work"] + [work['work_name'] for work in self.user_works]
                    self.work_dropdown.configure(values=work_names)
        finally:
            db.close()
    
    def _refresh_data(self, work_id: int):
        """Fetch analytics for specific work from database."""
        db = SessionLocal()
        try:
            engine = RBIAnalyticsEngine()
            return {
                'health': engine.get_work_health_score(db, work_id),
                'gaps': engine.get_critical_gaps(db, work_id),
                'equipment': engine.get_equipment_status(db, work_id),
                'team': engine.get_team_stats(db, work_id),
            }
        finally:
            db.close()
    
    def _on_work_selected(self, choice):
        """Handle work selection from dropdown."""
        if choice == "Select Work" or not self.user_works:
            self.current_work_id = None
            self._clear_analytics_display()
            return
        
        for work in self.user_works:
            if work['work_name'] == choice:
                self.current_work_id = work['work_id']
                self._display_analytics(self.current_work_id)
                break
    
    def _clear_analytics_display(self):
        """Clear the analytics display area."""
        if hasattr(self, 'analytics_container'):
            for widget in self.analytics_container.winfo_children():
                widget.destroy()
            
            placeholder = ctk.CTkLabel(
                self.analytics_container,
                text="Select a work to view analytics",
                font=("Segoe UI", 13),
                text_color=("gray60", "gray80"),
            )
            placeholder.pack(expand=True, pady=50)
    
    def _display_analytics(self, work_id: int):
        """Display analytics for the selected work."""
        data = self._refresh_data(work_id)
        
        if not data:
            return
        
        for widget in self.analytics_container.winfo_children():
            widget.destroy()
        
        work_name = ""
        for work in self.user_works:
            if work['work_id'] == work_id:
                work_name = work['work_name']
                break
        
        # Work header
        work_header = ctk.CTkFrame(self.analytics_container, fg_color="transparent")
        work_header.pack(fill="x", pady=(0, 24))
        
        work_title = ctk.CTkLabel(
            work_header,
            text=f"📊 {work_name}",
            font=("Segoe UI", 18, "bold"),
        )
        work_title.pack(anchor="w")
        
        work_subtitle = ctk.CTkLabel(
            work_header,
            text="Real-time RBI Assessment Analytics",
            font=("Segoe UI", 11),
            text_color=("gray60", "gray80"),
        )
        work_subtitle.pack(anchor="w", pady=(2, 0))
        
        # SECTION 1: HEALTH STATUS
        self._build_health_card(self.analytics_container, data['health'], work_id)
        
        # SECTION 2: CRITICAL GAPS & TEAM ACTIVITY (Side by side)
        metrics_row = ctk.CTkFrame(self.analytics_container, fg_color="transparent")
        metrics_row.pack(fill="both", expand=False, pady=(0, 18))
        metrics_row.grid_columnconfigure(0, weight=1)
        metrics_row.grid_columnconfigure(1, weight=1)
        
        gaps_container = ctk.CTkFrame(metrics_row, fg_color="transparent")
        gaps_container.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        self._build_gaps_section(gaps_container, data['gaps'])
        
        team_container = ctk.CTkFrame(metrics_row, fg_color="transparent")
        team_container.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        self._build_team_section(team_container, data['team'])
        
        # SECTION 3: EQUIPMENT PRIORITY
        self._build_equipment_section(self.analytics_container, data['equipment'])
    
    def _build_health_card(self, parent, health: Dict, work_id: int):
        """Enhanced health status card with visual indicators."""
        card = ctk.CTkFrame(
            parent,
            corner_radius=14,
            border_width=0,
            fg_color=("white", "gray17"),
        )
        card.pack(fill="x", pady=(0, 24))
        card.grid_columnconfigure(1, weight=1)
        
        # Left side: Status indicator
        left_frame = ctk.CTkFrame(card, fg_color="transparent", width=120)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        left_frame.grid_propagate(False)
        
        status_label = ctk.CTkLabel(
            left_frame,
            text=health['risk_level'].split(' - ')[0],
            font=("Segoe UI", 11, "bold"),
            text_color=health['status_color'],
        )
        status_label.pack()
        
        score_label = ctk.CTkLabel(
            left_frame,
            text=f"{health['health_score']}",
            font=("Segoe UI", 48, "bold"),
            text_color=health['status_color'],
        )
        score_label.pack()
        
        total_label = ctk.CTkLabel(
            left_frame,
            text="/ 100",
            font=("Segoe UI", 12),
            text_color=("gray60", "gray80"),
        )
        total_label.pack()
        
        # Right side: Metrics
        right_frame = ctk.CTkFrame(card, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 24), pady=24)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Metric boxes
        metrics = [
            ("Data Extraction", f"{health['extraction_rate']}%", "#3498db"),
            ("Critical Fields", f"{health['completeness_rate']}%", "#9b59b6"),
            ("Equipment", f"{health['extracted_equipment']}/{health['total_equipment']}", "#1abc9c"),
        ]
        
        for i, (label, value, color) in enumerate(metrics):
            metric_frame = ctk.CTkFrame(right_frame, fg_color=("gray90", "gray20"), corner_radius=10)
            metric_frame.pack(fill="x", pady=(0 if i == 0 else 12, 0))
            
            label_widget = ctk.CTkLabel(
                metric_frame,
                text=label,
                font=("Segoe UI", 10),
                text_color=("gray60", "gray80"),
            )
            label_widget.pack(anchor="w", padx=14, pady=(10, 4))
            
            value_widget = ctk.CTkLabel(
                metric_frame,
                text=value,
                font=("Segoe UI", 14, "bold"),
                text_color=color,
            )
            value_widget.pack(anchor="w", padx=14, pady=(0, 10))
    
    def _build_gaps_section(self, parent, gaps: List[Dict]):
        """Enhanced critical gaps section."""
        card = ctk.CTkFrame(
            parent,
            corner_radius=14,
            border_width=0,
            fg_color=("white", "gray17"),
        )
        card.pack(fill="both", expand=True)
        card.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            card,
            text="⚠️ Critical Data Gaps",
            font=("Segoe UI", 13, "bold"),
        )
        title.pack(anchor="w", padx=18, pady=(16, 12))
        
        if not gaps:
            no_gaps = ctk.CTkLabel(
                card,
                text="✓ All critical fields present",
                font=("Segoe UI", 12),
                text_color="#2ecc71",
            )
            no_gaps.pack(anchor="w", padx=18, pady=12)
            return
        
        gap_items = ctk.CTkFrame(card, fg_color="transparent")
        gap_items.pack(fill="both", expand=True, padx=12, pady=(0, 16))
        gap_items.grid_columnconfigure(0, weight=1)
        
        for i, gap in enumerate(gaps):
            gap_frame = ctk.CTkFrame(
                gap_items,
                fg_color=("gray90", "gray20"),
                corner_radius=10,
            )
            gap_frame.grid(row=i, column=0, sticky="ew", pady=(0, 8))
            gap_frame.grid_columnconfigure(1, weight=1)
            
            severity_color = "#e74c3c" if gap['severity'] == 'HIGH' else "#f39c12"
            
            severity_badge = ctk.CTkLabel(
                gap_frame,
                text="●",
                font=("Segoe UI", 14),
                text_color=severity_color,
                width=30,
            )
            severity_badge.grid(row=0, column=0, padx=12, pady=10)
            
            field_label = ctk.CTkLabel(
                gap_frame,
                text=gap['field'],
                font=("Segoe UI", 11, "bold"),
            )
            field_label.grid(row=0, column=1, sticky="w", padx=8, pady=10)
            
            count_label = ctk.CTkLabel(
                gap_frame,
                text=f"{gap['missing_count']} missing",
                font=("Segoe UI", 10, "bold"),
                text_color=severity_color,
            )
            count_label.grid(row=0, column=2, sticky="e", padx=12, pady=10)
    
    def _build_team_section(self, parent, team: Dict):
        """Enhanced team activity section."""
        card = ctk.CTkFrame(
            parent,
            corner_radius=14,
            border_width=0,
            fg_color=("white", "gray17"),
        )
        card.pack(fill="both", expand=True)
        card.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            card,
            text="📈 Work Activity",
            font=("Segoe UI", 13, "bold"),
        )
        title.pack(anchor="w", padx=18, pady=(16, 12))
        
        activity_items = ctk.CTkFrame(card, fg_color="transparent")
        activity_items.pack(fill="both", expand=True, padx=12, pady=(0, 16))
        activity_items.grid_columnconfigure(0, weight=1)
        
        metrics = [
            ("Extractions", team['extraction_actions'], "#3498db", "📤"),
            ("Corrections", team['correction_actions'], "#f39c12", "🔧"),
            ("Total Fixes", team['total_corrections'], "#2ecc71", "✓"),
        ]
        
        for i, (label, value, color, icon) in enumerate(metrics):
            metric_frame = ctk.CTkFrame(
                activity_items,
                fg_color=("gray90", "gray20"),
                corner_radius=10,
            )
            metric_frame.grid(row=i, column=0, sticky="ew", pady=(0, 8))
            
            icon_label = ctk.CTkLabel(
                metric_frame,
                text=icon,
                font=("Segoe UI", 16),
                width=50,
            )
            icon_label.pack(side="left", padx=12, pady=12)
            
            text_frame = ctk.CTkFrame(metric_frame, fg_color="transparent")
            text_frame.pack(side="left", fill="both", expand=True, padx=(0, 12))
            
            label_widget = ctk.CTkLabel(
                text_frame,
                text=label,
                font=("Segoe UI", 10),
                text_color=("gray60", "gray80"),
            )
            label_widget.pack(anchor="w")
            
            value_widget = ctk.CTkLabel(
                text_frame,
                text=str(value),
                font=("Segoe UI", 16, "bold"),
                text_color=color,
            )
            value_widget.pack(anchor="w")
    
    def _build_equipment_section(self, parent, equipment: List[Dict]):
        """Enhanced equipment priority section."""
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x")
        section.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            section,
            text="🔧 Equipment Priority (Incomplete First)",
            font=("Segoe UI", 13, "bold"),
        )
        title.pack(anchor="w", pady=(0, 12))
        
        if not equipment:
            no_eq = ctk.CTkLabel(
                section,
                text="No equipment data",
                font=("Segoe UI", 11),
                text_color=("gray60", "gray80"),
            )
            no_eq.pack(anchor="w")
            return
        
        eq_list = ctk.CTkFrame(section, fg_color="transparent")
        eq_list.pack(fill="both", expand=False)
        eq_list.grid_columnconfigure(0, weight=1)
        
        for i, eq in enumerate(equipment[:10]):
            eq_frame = ctk.CTkFrame(
                eq_list,
                fg_color=("white", "gray20"),
                corner_radius=10,
                border_width=1,
                border_color=("gray85", "gray30"),
            )
            eq_frame.grid(row=i, column=0, sticky="ew", pady=(0, 6))
            eq_frame.grid_columnconfigure(2, weight=1)
            
            status_label = ctk.CTkLabel(
                eq_frame,
                text=eq['status'],
                font=("Segoe UI", 12, "bold"),
                text_color=eq['color'],
                width=40,
            )
            status_label.grid(row=0, column=0, padx=12, pady=10)
            
            eq_label = ctk.CTkLabel(
                eq_frame,
                text=f"{eq['equipment_no']} • {eq['components']} components",
                font=("Segoe UI", 11),
            )
            eq_label.grid(row=0, column=2, sticky="w", padx=8, pady=10)
            
            # Progress bar
            progress_value = eq['completeness'] / 100.0
            progress_frame = ctk.CTkFrame(eq_frame, fg_color=("gray85", "gray30"), corner_radius=4, height=6)
            progress_frame.grid(row=0, column=3, sticky="ew", padx=(8, 12), pady=10)
            
            progress_fill = ctk.CTkFrame(progress_frame, fg_color=eq['color'], corner_radius=4, height=6)
            progress_fill.place(relwidth=progress_value, relheight=1)
            
            complete_label = ctk.CTkLabel(
                eq_frame,
                text=f"{eq['completeness']}%",
                font=("Segoe UI", 10, "bold"),
                text_color=eq['color'],
                width=50,
            )
            complete_label.grid(row=0, column=4, sticky="e", padx=12, pady=10)
        
        if len(equipment) > 10:
            more_label = ctk.CTkLabel(
                section,
                text=f"... and {len(equipment) - 10} more equipment items",
                font=("Segoe UI", 10),
                text_color=("gray60", "gray80"),
            )
            more_label.pack(anchor="w", pady=(8, 0))
    
    def show(self) -> None:
        """Display Analytics Dashboard with improved layout."""
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        root_frame = ctk.CTkFrame(self.parent, corner_radius=0, fg_color="transparent")
        root_frame.pack(expand=True, fill="both", padx=32, pady=24)
        
        root_frame.grid_rowconfigure(2, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)
        
        # HEADER
        header = ctk.CTkFrame(root_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 24))
        header.grid_columnconfigure(0, weight=1)
        
        back_btn = ctk.CTkButton(
            header,
            text="← Back",
            command=self.controller.show_main_menu,
            width=100,
            height=36,
            font=("Segoe UI", 10),
            fg_color="transparent",
            text_color=("gray40", "gray80"),
            hover_color=("gray85", "gray30"),
            border_width=0,
        )
        back_btn.pack(side="left")
        
        title_label = ctk.CTkLabel(
            header,
            text="RBI Analytics Dashboard",
            font=("Segoe UI", 26, "bold"),
        )
        title_label.pack(side="right")
        
        # WORK SELECTION SECTION
        selection_frame = ctk.CTkFrame(root_frame, fg_color="transparent")
        selection_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        selection_frame.grid_columnconfigure(1, weight=1)
        
        selection_label = ctk.CTkLabel(
            selection_frame,
            text="Select Work:",
            font=("Segoe UI", 12, "bold"),
        )
        selection_label.grid(row=0, column=0, sticky="w", padx=(0, 12))
        
        self._load_user_works()
        
        work_names = ["Select Work"] + [work['work_name'] for work in self.user_works]
        self.work_dropdown = ctk.CTkComboBox(
            selection_frame,
            values=work_names,
            variable=self.selected_work_var,
            command=self._on_work_selected,
            width=350,
            height=36,
            font=("Segoe UI", 11),
            dropdown_font=("Segoe UI", 11),
        )
        self.work_dropdown.grid(row=0, column=1, sticky="w")
        
        # ANALYTICS CONTAINER
        self.analytics_container = ctk.CTkScrollableFrame(
            root_frame,
            corner_radius=0,
            border_width=0,
            fg_color="transparent",
        )
        self.analytics_container.grid(row=2, column=0, sticky="nsew")
        self.analytics_container.grid_columnconfigure(0, weight=1)
        
        self._clear_analytics_display()
        
        # REFRESH BUTTON
        refresh_frame = ctk.CTkFrame(root_frame, fg_color="transparent")
        refresh_frame.grid(row=3, column=0, sticky="e", pady=(20, 0))
        
        refresh_btn = ctk.CTkButton(
            refresh_frame,
            text="🔄 Refresh",
            command=self._refresh_all,
            height=36,
            font=("Segoe UI", 11),
            width=140,
            fg_color="#3498db",
            hover_color="#2980b9",
        )
        refresh_btn.pack(side="right")
    
    def _refresh_all(self):
        """Refresh all data including works list and current analytics."""
        self._load_user_works()
        
        if self.current_work_id:
            self._display_analytics(self.current_work_id)
        else:
            self._clear_analytics_display()