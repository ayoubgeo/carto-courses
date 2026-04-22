#!/bin/bash
# deploy.sh - runs on cPanel server via cron job at 8:00 AM daily

REPO="/home2/cartoma/courses-repo"
PUBLIC="/home2/cartoma/public_html"
LOG="/home2/cartoma/deploy.log"

echo "========================================" >> $LOG
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Deploy started" >> $LOG

# Pull latest from GitHub
cd $REPO
git pull origin main >> $LOG 2>&1

# Copy course HTML files directly to public_html root
cp -u $REPO/courses/*.html $PUBLIC/ 2>/dev/null && echo "Courses copied." >> $LOG

# Copy updated index -- both with and without extension
cp $REPO/geoaicourses.html $PUBLIC/geoaicourses.html 2>/dev/null && echo "geoaicourses.html updated." >> $LOG
cp $REPO/geoaicourses.html $PUBLIC/geoaicourses 2>/dev/null && echo "geoaicourses (no ext) updated." >> $LOG

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Deploy done." >> $LOG
echo "========================================" >> $LOG
