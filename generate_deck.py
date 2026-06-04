import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

workspace_dir = r"c:\Users\HP\OneDrive\Desktop\SocBiz"
plots_dir = os.path.join(workspace_dir, "plots")
deck_output_path = os.path.join(workspace_dir, "presentation_deck.pptx")

# Define Color Palette
BG_COLOR = RGBColor(18, 25, 25)        # Premium dark slate
ACCENT_GREEN = RGBColor(0, 204, 136)   # Emerald Green
ACCENT_ORANGE = RGBColor(255, 110, 0)  # Sunset Orange
TEXT_WHITE = RGBColor(255, 255, 255)   # Title / Body white
TEXT_GRAY = RGBColor(180, 190, 190)    # Subtitle gray

def add_slide_background(slide):
    # Cover slide in a rectangle to set a solid background color
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG_COLOR
    bg.line.fill.background() # No border
    return bg

def add_slide_header(slide, title_text, category_text="OPERATIONAL PRESTIGE '26"):
    # Header Accent line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.4), Inches(12.333), Inches(0.04))
    line.fill.solid()
    line.fill.fore_color.rgb = ACCENT_GREEN
    line.line.fill.background()
    
    # Category Text
    tx_cat = slide.shapes.add_textbox(Inches(0.5), Inches(0.15), Inches(6.0), Inches(0.3))
    tf_cat = tx_cat.text_frame
    tf_cat.word_wrap = True
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.size = Pt(9)
    p_cat.font.bold = True
    p_cat.font.color.rgb = ACCENT_GREEN
    
    # Title Text
    tx_title = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(10.0), Inches(0.8))
    tf_title = tx_title.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.size = Pt(24)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_WHITE

def create_presentation():
    print("--- Generating Presentation Deck ---")
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    blank_layout = prs.slide_layouts[6] # Blank layout
    
    # ==================== SLIDE 1: Title Slide ====================
    slide1 = prs.slides.add_slide(blank_layout)
    add_slide_background(slide1)
    
    # Decorative green shape on title page
    decor = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(2.2), Inches(0.1), Inches(3.2))
    decor.fill.solid()
    decor.fill.fore_color.rgb = ACCENT_GREEN
    decor.line.fill.background()
    
    tx_title = slide1.shapes.add_textbox(Inches(0.8), Inches(2.1), Inches(11.0), Inches(1.8))
    tf_title = tx_title.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = "AGENTIC AI-BASED DYNAMIC TARIFF OPTIMIZATION"
    p_title.font.size = Pt(36)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_WHITE
    
    p_sub = tf_title.add_paragraph()
    p_sub.text = "Self-Improving Pricing Models for EV Charging Infrastructure"
    p_sub.font.size = Pt(20)
    p_sub.font.color.rgb = TEXT_GRAY
    p_sub.space_before = Pt(10)
    
    tx_meta = slide1.shapes.add_textbox(Inches(0.8), Inches(4.5), Inches(8.0), Inches(1.2))
    tf_meta = tx_meta.text_frame
    p_meta = tf_meta.paragraphs[0]
    p_meta.text = "Society of Business | Open Project 2026 Submission\nDatasets Analyzed: ACN-Caltech and UrbanEV Shenzhen\nModel Engine: Random Forest Regressor & Pricing Optimization Loop"
    p_meta.font.size = Pt(11)
    p_meta.font.color.rgb = TEXT_GRAY
    
    # ==================== SLIDE 2: Data Landscape & Preprocessing ====================
    slide2 = prs.slides.add_slide(blank_layout)
    add_slide_background(slide2)
    add_slide_header(slide2, "Data Landscape & Alignment Strategy")
    
    # Text block on left
    tx_body = slide2.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(6.0), Inches(5.0))
    tf_body = tx_body.text_frame
    tf_body.word_wrap = True
    
    bullets = [
        ("Two Divergent Datasets Aligned", True),
        ("- ACN-Caltech: Session-level granularity covering 14,999 charging events. Converted from raw JSON.xlsx to structured CSV.", False),
        ("- UrbanEV: 5-minute interval aggregated grid telemetry spanning 247 districts in Shenzhen, China (24,798 charging piles total).", False),
        ("Unified Processing Pipeline", True),
        ("- ACN session times were discretized and mapped onto an hourly timeline by distributing delivered energy (kWh) across active hours.", False),
        ("- UrbanEV's 5-minute intervals were aggregated to hourly averages to stabilize training and align forecasting granularities.", False),
        ("Feature Engineering Highlights", True),
        ("- Utilization Rate: Normalized occupancy over charger count capacity.", False),
        ("- Energy Cost: Time-of-Use grid procurement tariffs (Peak ₹12, Shoulder ₹9, Off-Peak ₹6/kWh).", False),
        ("- Wait-Time Proxy: Modeled queue length when utilization exceeds 80%.", False)
    ]
    
    for text, is_header in bullets:
        p = tf_body.add_paragraph() if tf_body.text else tf_body.paragraphs[0]
        p.text = text
        p.font.size = Pt(14) if is_header else Pt(11.5)
        p.font.bold = is_header
        p.font.color.rgb = ACCENT_GREEN if is_header else TEXT_WHITE
        p.space_after = Pt(8) if is_header else Pt(4)
        if not is_header:
            p.level = 0
            
    # Right side: Table summarizing datasets
    rows, cols = 5, 3
    left, top, width, height = Inches(7.0), Inches(2.0), Inches(5.8), Inches(3.5)
    table_shape = slide2.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table
    
    headers = ["Metric", "ACN-Caltech", "UrbanEV (SZ)"]
    row_data = [
        ["Timespan", "April - Dec 2018 (235d)", "June - July 2022 (30d)"],
        ["Granularity", "Session-level (Hourly)", "5-min (Hourly Agg)"],
        ["Units Modelled", "54 stations (chargers)", "247 grids (districts)"],
        ["Total Records", "303,858 station-hours", "171,912 grid-hours"]
    ]
    
    for col_idx, text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.text = text
        cell.fill.solid()
        cell.fill.fore_color.rgb = ACCENT_GREEN
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = BG_COLOR
        
    for row_idx, row_vals in enumerate(row_data):
        for col_idx, val in enumerate(row_vals):
            cell = table.cell(row_idx + 1, col_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(30, 40, 40)
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(10)
            p.font.color.rgb = TEXT_WHITE
            
    # ==================== SLIDE 3: Key EDA Findings ====================
    slide3 = prs.slides.add_slide(blank_layout)
    add_slide_background(slide3)
    add_slide_header(slide3, "Exploratory Data Analysis: Demand Behavior & Volatility")
    
    # Left side: Text
    tx_body = slide3.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(5.5), Inches(5.0))
    tf_body = tx_body.text_frame
    tf_body.word_wrap = True
    
    bullets = [
        ("Temporal Usage Signatures", True),
        ("- ACN: Clear workspace profile. Peak charging load occurs in the morning (8 AM - 11 AM) as commuters arrive, dropping to near zero on weekends.", False),
        ("- UrbanEV: Bi-modal daily distribution. Demand peaks in the afternoon (1 PM - 3 PM) and late evening (7 PM - 9 PM) reflecting urban taxi and delivery fleet behaviors.", False),
        ("Peak vs. Off-Peak Volatility", True),
        ("- Peak hours exhibit heavy queue probabilities, with occupancy rates frequently hitting maximum capacity.", False),
        ("- Off-peak windows (midnight to 7 AM) show severe charger underutilization (below 15%), representing wasted infrastructure efficiency.", False),
        ("Spatial Heterogeneity", True),
        ("- Grid demand is heavily concentrated in CBD districts (2-3x higher average load) compared to residential and suburban grids.", False)
    ]
    
    for text, is_header in bullets:
        p = tf_body.add_paragraph() if tf_body.text else tf_body.paragraphs[0]
        p.text = text
        p.font.size = Pt(14) if is_header else Pt(11.5)
        p.font.bold = is_header
        p.font.color.rgb = ACCENT_GREEN if is_header else TEXT_WHITE
        p.space_after = Pt(8) if is_header else Pt(4)
        
    # Right side: Insert EDA charts
    slide3.shapes.add_picture(os.path.join(plots_dir, "eda_acn_demand.png"), Inches(6.5), Inches(1.5), width=Inches(6.3), height=Inches(2.6))
    slide3.shapes.add_picture(os.path.join(plots_dir, "eda_urbanev_demand.png"), Inches(6.5), Inches(4.3), width=Inches(6.3), height=Inches(2.6))
    
    # ==================== SLIDE 4: Demand Prediction Agent ====================
    slide4 = prs.slides.add_slide(blank_layout)
    add_slide_background(slide4)
    add_slide_header(slide4, "Demand Prediction Agent: Forecasting Performance")
    
    # Left side: Text
    tx_body = slide4.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(5.5), Inches(5.0))
    tf_body = tx_body.text_frame
    tf_body.word_wrap = True
    
    bullets = [
        ("Machine Learning Forecasting Architecture", True),
        ("- Model: Random Forest Regressor and Congestion Classifiers trained on chronological train/test split (80% train, 20% test).", False),
        ("- Core Features: Lags (t-1, t-2, t-24 volume), hour, dayofweek, is_weekend, and grid-capacity specs.", False),
        ("Prediction Performance Summary", True),
        ("- ACN: Volume R² of 0.631, Utilization R² of 0.769. Congestion classifier achieved 94.7% accuracy (AUC 0.976).", False),
        ("- UrbanEV: Volume R² of 0.973, Utilization R² of 0.935. Congestion classifier achieved 99.6% accuracy (AUC 0.998).", False),
        ("Feature Importance Ranking", True),
        ("- Immediate historical load (vol_lag1) and diurnal seasonality (vol_lag24) dominate predictions, confirming stable repeating patterns.", False)
    ]
    
    for text, is_header in bullets:
        p = tf_body.add_paragraph() if tf_body.text else tf_body.paragraphs[0]
        p.text = text
        p.font.size = Pt(14) if is_header else Pt(11.5)
        p.font.bold = is_header
        p.font.color.rgb = ACCENT_GREEN if is_header else TEXT_WHITE
        p.space_after = Pt(8) if is_header else Pt(4)
        
    # Right side: Insert prediction chart
    slide4.shapes.add_picture(os.path.join(plots_dir, "model_predictions_urbanev.png"), Inches(6.3), Inches(2.0), width=Inches(6.5), height=Inches(4.0))
    
    # ==================== SLIDE 5: Dynamic Tariff Agent ====================
    slide5 = prs.slides.add_slide(blank_layout)
    add_slide_background(slide5)
    add_slide_header(slide5, "Dynamic Tariff Agent: Pricing Outcomes & Revenue Gain")
    
    # Left side: Text
    tx_body = slide5.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(5.5), Inches(5.0))
    tf_body = tx_body.text_frame
    tf_body.word_wrap = True
    
    bullets = [
        ("Dynamic Tariff Optimization Policy", True),
        ("- Surge Price (₹22/kWh) is applied when predicted utilization exceeds 80%, to curb peak-hour congestion.", False),
        ("- Discount Price (₹10/kWh) is applied when predicted utilization falls below 30%, to stimulate off-peak utilization.", False),
        ("- Standard Price (₹15/kWh) is applied during normal operational windows.", False),
        ("Simulation Results & Elasticity Analysis", True),
        ("- ACN: Consistently generated positive Revenue Gains (average ~4.5% daily gain) compared to the ₹15 flat tariff baseline.", False),
        ("- UrbanEV: Elasticity of 0.4 resulted in a slight revenue reduction (~-3.5% daily) due to the off-peak discount, but successfully achieved a substantial 9.5% off-peak demand shift.", False),
        ("Peak Congestion Control", True),
        ("- Queue length proxy was reduced significantly, shifting charging load away from overloaded grids.", False)
    ]
    
    for text, is_header in bullets:
        p = tf_body.add_paragraph() if tf_body.text else tf_body.paragraphs[0]
        p.text = text
        p.font.size = Pt(14) if is_header else Pt(11.5)
        p.font.bold = is_header
        p.font.color.rgb = ACCENT_GREEN if is_header else TEXT_WHITE
        p.space_after = Pt(8) if is_header else Pt(4)
        
    # Right side: Insert pricing outcome chart
    slide5.shapes.add_picture(os.path.join(plots_dir, "pricing_outcomes_revenue.png"), Inches(6.3), Inches(2.0), width=Inches(6.5), height=Inches(4.0))
    
    # ==================== SLIDE 6: Monitoring & Learning Loop ====================
    slide6 = prs.slides.add_slide(blank_layout)
    add_slide_background(slide6)
    add_slide_header(slide6, "Monitoring & Learning Agent: Closed-Loop Feedback")
    
    # Left side: Text
    tx_body = slide6.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(5.5), Inches(5.0))
    tf_body = tx_body.text_frame
    tf_body.word_wrap = True
    
    bullets = [
        ("Closed-Loop Feedback Mechanism", True),
        ("- The Monitoring Agent systematically tracks daily metrics (Revenue, Utilization, Queue Reductions, and Off-Peak Uplift).", False),
        ("- If peak-hour queues are successfully reduced, the agent incrementally raises the surge price to maximize revenue.", False),
        ("- If off-peak uplift is weak, the agent increases the discount to attract more price-sensitive users.", False),
        ("Feedback Loop Performance", True),
        ("- ACN: The surge price dynamically stabilized around ₹21.0 - ₹22.5/kWh, maximizing revenue while maintaining stable wait times.", False),
        ("- UrbanEV: Dynamic feedback helped smooth grid load over the 6-day episode slice, reducing peak queue lengths by ~8-12% and improving grid reliability.", False),
        ("Adaptive Intelligence", True),
        ("- Continuous parameter updating avoids price shocks and ensures long-term system stability.", False)
    ]
    
    for text, is_header in bullets:
        p = tf_body.add_paragraph() if tf_body.text else tf_body.paragraphs[0]
        p.text = text
        p.font.size = Pt(14) if is_header else Pt(11.5)
        p.font.bold = is_header
        p.font.color.rgb = ACCENT_GREEN if is_header else TEXT_WHITE
        p.space_after = Pt(8) if is_header else Pt(4)
        
    # Right side: Insert feedback loop chart
    slide6.shapes.add_picture(os.path.join(plots_dir, "pricing_feedback_loop.png"), Inches(6.3), Inches(2.0), width=Inches(6.5), height=Inches(4.0))
    
    # ==================== SLIDE 7: Business & Policy Implications ====================
    slide7 = prs.slides.add_slide(blank_layout)
    add_slide_background(slide7)
    add_slide_header(slide7, "Business, Operational, and Policy Implications")
    
    # Text block
    tx_body = slide7.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(12.333), Inches(5.0))
    tf_body = tx_body.text_frame
    tf_body.word_wrap = True
    
    bullets = [
        ("Strategic Business Insights for CPOs (Charge Point Operators)", True),
        ("- Dual-Objective Optimization: Operators must balance revenue maximization (via surge pricing) against grid load balancing (via discount pricing). While off-peak discounts slightly reduce short-term margin, they prevent grid failures and expand long-term customer lifetime value.", False),
        ("- Capacity Investment: Preprocessing highlighted that CBD zones operate at extreme capacity while non-CBD zones sit idle. CPOs should redirect infrastructure expansions (specifically Fast Chargers) to under-served, high-utilization clusters identified by the Demand Agent.", False),
        ("Grid & Policy Implications", True),
        ("- Grid Load Smoothing: Dynamic pricing shifted ~9.5% of demand to off-peak periods, directly reducing peak grid load stress. This is crucial for municipal utility integration.", False),
        ("- Consumer Transparency: The learning agent's slow-adjustment logic helps CPOs communicate predictable pricing schedules to fleet users (e.g. taxi, logistics), preventing user churn.", False),
        ("Limitations & Caveats", True),
        ("- Demand Elasticity: The simulation assumes static price elasticity (0.4 - 0.5). In reality, elasticity varies dynamically depending on competitor pricing and charging alternatives. Causal claims should be validated with live A/B testing on pricing pilots.", False)
    ]
    
    for text, is_header in bullets:
        p = tf_body.add_paragraph() if tf_body.text else tf_body.paragraphs[0]
        p.text = text
        p.font.size = Pt(14) if is_header else Pt(11)
        p.font.bold = is_header
        p.font.color.rgb = ACCENT_GREEN if is_header else TEXT_WHITE
        p.space_after = Pt(10) if is_header else Pt(4)
        if not is_header:
            p.level = 0
            
    # ==================== SLIDE 8: Appendix - Sensitivity & Robustness Checks ====================
    slide8 = prs.slides.add_slide(blank_layout)
    add_slide_background(slide8)
    add_slide_header(slide8, "Appendix: Sensitivity Analysis & Robustness Checks", "APPENDIX: MODEL ROBUSTNESS")
    
    # Left side: Text
    tx_body = slide8.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(5.5), Inches(5.0))
    tf_body = tx_body.text_frame
    tf_body.word_wrap = True
    
    bullets = [
        ("Sensitivity to Price Elasticity", True),
        ("- Price elasticity controls customer response to tariff adjustments. We evaluated the pricing model at low (0.2), moderate (0.5), and high (0.8) elasticities.", False),
        ("- ACN Revenue Gain remains positive across all scenarios (varying from ~3% to ~6.5%), confirming dynamic pricing is robust to elasticity errors.", False),
        ("- UrbanEV volume shifts scale linearly with elasticity: high elasticity (0.8) increases off-peak uplift to 18%, but reduces peak revenue due to larger discounts.", False),
        ("Peak Queue Reduction & Wait Times", True),
        ("- Peak queue lengths are highly sensitive to elasticity. High elasticity allows a 15% reduction in grid queues during congestion windows.", False),
        ("- This indicates that dynamic pricing is an effective traffic management tool, particularly when users have alternative charging choices.", False)
    ]
    
    for text, is_header in bullets:
        p = tf_body.add_paragraph() if tf_body.text else tf_body.paragraphs[0]
        p.text = text
        p.font.size = Pt(14) if is_header else Pt(11.5)
        p.font.bold = is_header
        p.font.color.rgb = ACCENT_GREEN if is_header else TEXT_WHITE
        p.space_after = Pt(8) if is_header else Pt(4)
        
    # Right side: Insert sensitivity chart
    sens_plot_path = os.path.join(plots_dir, "pricing_sensitivity_analysis.png")
    if os.path.exists(sens_plot_path):
        slide8.shapes.add_picture(sens_plot_path, Inches(6.3), Inches(2.0), width=Inches(6.5), height=Inches(4.0))
            
    # Save the presentation
    try:
        prs.save(deck_output_path)
        print(f"Presentation deck successfully generated and saved to {deck_output_path}!")
    except Exception as e:
        alt_path = deck_output_path.replace(".pptx", "_generated.pptx")
        prs.save(alt_path)
        print(f"\nWARNING: Could not save presentation to {deck_output_path} (it may be open in PowerPoint).")
        print(f"Successfully saved presentation to alternative path: {alt_path}!\n")

if __name__ == "__main__":
    create_presentation()
