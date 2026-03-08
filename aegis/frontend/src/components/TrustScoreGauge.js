/** 
 * AEGIS — Trust Score Gauge (D3.js) 
 * Animated radial gauge showing the composite Trust Score (0–100).	
 */	

'use client'; 

import { useEffect, useRef } from 'react'; 
import * as d3 from 'd3';	

function getScoreColor(score) {	
    if (score >= 80) return '#06d6a0'; 
    if (score >= 60) return '#22c55e'; 
    if (score >= 40) return '#eab308';	
    if (score >= 20) return '#f97316';	
    return '#ef4444';	
} 

function getScoreLabel(score) { 
    if (score >= 80) return 'Excellent'; 
    if (score >= 60) return 'Good'; 
    if (score >= 40) return 'Moderate'; 
    if (score >= 20) return 'Low';	
    return 'Critical';	
} 

export default function TrustScoreGauge({ score = 0, size = 280 }) { 
    const svgRef = useRef(null);	

    useEffect(() => {	
        if (!svgRef.current) return; 

        const svg = d3.select(svgRef.current); 
        svg.selectAll('*').remove();	

        const width = size;	
        const height = size;	
        const radius = (Math.min(width, height) / 2) - 20; 
        const thickness = 18; 
        const color = getScoreColor(score);	

        const g = svg 
            .attr('width', width)	
            .attr('height', height)	
            .append('g') 
            .attr('transform', `translate(${width / 2}, ${height / 2})`); 

        // Background arc	
        const bgArc = d3.arc() 
            .innerRadius(radius - thickness)	
            .outerRadius(radius) 
            .startAngle(-Math.PI * 0.75)	
            .endAngle(Math.PI * 0.75)	
            .cornerRadius(thickness / 2); 

        g.append('path') 
            .attr('d', bgArc)	
            .attr('fill', 'rgba(148, 163, 184, 0.08)') 
            .attr('stroke', 'rgba(148, 163, 184, 0.05)') 
            .attr('stroke-width', 0.5); 

        // Score arc (animated)	
        const scoreAngle = -Math.PI * 0.75 + (Math.PI * 1.5 * score / 100);	

        const scoreArc = d3.arc() 
            .innerRadius(radius - thickness) 
            .outerRadius(radius)	
            .startAngle(-Math.PI * 0.75) 
            .cornerRadius(thickness / 2);	

        // Gradient 
        const gradient = svg.append('defs') 
            .append('linearGradient')	
            .attr('id', 'score-gradient')	
            .attr('x1', '0%').attr('y1', '0%') 
            .attr('x2', '100%').attr('y2', '0%');	

        gradient.append('stop').attr('offset', '0%').attr('stop-color', '#4361ee');	
        gradient.append('stop').attr('offset', '100%').attr('stop-color', color); 

        // Glow filter
        const filter = svg.append('defs').append('filter').attr('id', 'glow');
        filter.append('feGaussianBlur').attr('stdDeviation', '4').attr('result', 'coloredBlur');
        const feMerge = filter.append('feMerge');
        feMerge.append('feMergeNode').attr('in', 'coloredBlur');
        feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

        const scorePath = g.append('path')
            .attr('fill', 'url(#score-gradient)')
            .attr('filter', 'url(#glow)')
            .attr('d', scoreArc({ endAngle: -Math.PI * 0.75 }));

        // Animate
        scorePath.transition()
            .duration(1500)
            .ease(d3.easeElasticOut.amplitude(1).period(0.5))
            .attrTween('d', () => {
                const interpolate = d3.interpolate(-Math.PI * 0.75, scoreAngle);
                return (t) => scoreArc({ endAngle: interpolate(t) });
            });

        // Score text
        const scoreText = g.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '-10')
            .attr('fill', color)
            .attr('font-size', '56px')
            .attr('font-weight', '800')
            .attr('font-family', "'Inter', sans-serif")
            .attr('letter-spacing', '-0.04em')
            .text('0');

        scoreText.transition()
            .duration(1500)
            .ease(d3.easeCubicOut)
            .tween('text', () => {
                const interpolate = d3.interpolateRound(0, Math.round(score));
                return (t) => scoreText.text(interpolate(t));
            });

        // Label
        g.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '20')
            .attr('fill', '#94a3b8')
            .attr('font-size', '13px')
            .attr('font-weight', '600')
            .attr('text-transform', 'uppercase')
            .attr('letter-spacing', '0.1em')
            .text('TRUST SCORE');

        // Status label
        g.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '42')
            .attr('fill', color)
            .attr('font-size', '14px')
            .attr('font-weight', '700')
            .text(getScoreLabel(score));

        // Tick marks
        const tickCount = 10;
        for (let i = 0; i <= tickCount; i++) {
            const angle = -Math.PI * 0.75 + (Math.PI * 1.5 * i / tickCount);
            const isMajor = i % 5 === 0;
            const r1 = radius + 6;
            const r2 = radius + (isMajor ? 16 : 10);

            g.append('line')
                .attr('x1', r1 * Math.cos(angle))
                .attr('y1', r1 * Math.sin(angle))
                .attr('x2', r2 * Math.cos(angle))
                .attr('y2', r2 * Math.sin(angle))
                .attr('stroke', isMajor ? '#64748b' : 'rgba(148, 163, 184, 0.2)')
                .attr('stroke-width', isMajor ? 2 : 1);

            if (isMajor) {
                g.append('text')
                    .attr('x', (r2 + 14) * Math.cos(angle))
                    .attr('y', (r2 + 14) * Math.sin(angle))
                    .attr('text-anchor', 'middle')
                    .attr('dominant-baseline', 'middle')
                    .attr('fill', '#64748b')
                    .attr('font-size', '10px')
                    .attr('font-weight', '600')
                    .text(i * 10);
            }
        }

    }, [score, size]);

    return (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '16px' }}>
            <svg ref={svgRef} />
        </div>
    );
}
