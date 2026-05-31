"""
Video Processing Pipeline
Handles scene detection, frame extraction, and visual embeddings
"""
import os
import cv2
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
from dataclasses import dataclass
import json

@dataclass
class Scene:
    id: int
    start_time: float
    end_time: float
    start_frame: int
    end_frame: int
    thumbnail_path: Optional[str] = None
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

@dataclass
class Frame:
    id: int
    scene_id: int
    timestamp: float
    frame_number: int
    path: str
    embedding: Optional[List[float]] = None

class SceneDetector:
    def __init__(self, threshold: float = 30.0):
        self.threshold = threshold
        
    def detect_scenes_opencv(self, video_path: str) -> List[Scene]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        scenes = []
        prev_frame = None
        scene_start_frame = 0
        scene_id = 0
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (320, 180))
            
            if prev_frame is not None:
                diff = cv2.absdiff(gray, prev_frame)
                mean_diff = np.mean(diff)
                
                if mean_diff > self.threshold:
                    scenes.append(Scene(
                        id=scene_id,
                        start_time=scene_start_frame / fps,
                        end_time=frame_count / fps,
                        start_frame=scene_start_frame,
                        end_frame=frame_count
                    ))
                    scene_id += 1
                    scene_start_frame = frame_count
            
            prev_frame = gray
            frame_count += 1
            
            if frame_count % 1000 == 0:
                print(f"Processed {frame_count}/{total_frames} frames...")
        
        if scene_start_frame < frame_count:
            scenes.append(Scene(
                id=scene_id,
                start_time=scene_start_frame / fps,
                end_time=frame_count / fps,
                start_frame=scene_start_frame,
                end_frame=frame_count
            ))
        
        cap.release()
        return scenes

class FrameExtractor:
    def __init__(self, output_dir: str = "data/frames"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_scene_thumbnails(self, video_path: str, scenes: List[Scene], movie_name: str) -> List[Scene]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        for scene in scenes:
            middle_frame = (scene.start_frame + scene.end_frame) // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
            
            ret, frame = cap.read()
            if ret:
                thumb_name = f"{movie_name}_scene_{scene.id:04d}.jpg"
                thumb_path = self.output_dir / thumb_name
                thumb = cv2.resize(frame, (320, 180))
                cv2.imwrite(str(thumb_path), thumb)
                scene.thumbnail_path = str(thumb_path)
        
        cap.release()
        return scenes
    
    def extract_keyframes(self, video_path: str, scenes: List[Scene], movie_name: str, frames_per_scene: int = 3) -> List[Frame]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = []
        frame_id = 0
        
        for scene in scenes:
            total_scene_frames = scene.end_frame - scene.start_frame
            step = total_scene_frames // (frames_per_scene + 1)
            
            for i in range(1, frames_per_scene + 1):
                frame_num = scene.start_frame + i * step
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                
                ret, frame = cap.read()
                if ret:
                    timestamp = frame_num / fps
                    frame_name = f"{movie_name}_scene{scene.id}_frame{frame_id:04d}.jpg"
                    frame_path = self.output_dir / frame_name
                    resized = cv2.resize(frame, (640, 360))
                    cv2.imwrite(str(frame_path), resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    
                    frames.append(Frame(
                        id=frame_id,
                        scene_id=scene.id,
                        timestamp=timestamp,
                        frame_number=frame_num,
                        path=str(frame_path)
                    ))
                    frame_id += 1
        
        cap.release()
        return frames

class VideoPipeline:
    def __init__(self, output_dir: str = "data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.scene_detector = SceneDetector()
        self.frame_extractor = FrameExtractor(str(self.output_dir / "frames"))
    
    def process_video(self, video_path: str, movie_name: str) -> Dict:
        print(f"\n{'='*60}\nProcessing: {movie_name}\nVideo: {video_path}\n{'='*60}\n")
        
        print("Step 1: Detecting scenes...")
        scenes = self.scene_detector.detect_scenes_opencv(video_path)
        print(f"  Found {len(scenes)} scenes")
        
        print("\nStep 2: Extracting scene thumbnails...")
        scenes = self.frame_extractor.extract_scene_thumbnails(video_path, scenes, movie_name)
        
        print("\nStep 3: Extracting keyframes...")
        frames = self.frame_extractor.extract_keyframes(video_path, scenes, movie_name, frames_per_scene=3)
        
        result = {
            "movie_name": movie_name,
            "video_path": video_path,
            "total_scenes": len(scenes),
            "total_keyframes": len(frames),
            "scenes": [{"id": s.id, "start_time": s.start_time, "end_time": s.end_time, "duration": s.duration, "thumbnail": s.thumbnail_path} for s in scenes],
            "keyframes": [{"id": f.id, "scene_id": f.scene_id, "timestamp": f.timestamp, "path": f.path} for f in frames]
        }
        
        output_file = self.output_dir / f"{movie_name}_video_metadata.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n✓ Processing complete! Metadata saved to: {output_file}")
        return result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process video for scene detection")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("--name", required=True, help="Movie name")
    parser.add_argument("--output", default="data", help="Output directory")
    args = parser.parse_args()
    
    pipeline = VideoPipeline(output_dir=args.output)
    result = pipeline.process_video(args.video, args.name)