            self.image_labels[slot_index].setStyleSheet("""
                QLabel {
                    border: 1px solid #cccccc;
                    border-radius: 8px;
                    background-color: white;
                }
            """)
            
            # Store the image path
            self.image_paths[slot_index] = image_path
            
            # Enable action buttons
            self.image_slots[slot_index].download_btn.setEnabled(True)
            self.image_slots[slot_index].pick_btn.setEnabled(True)
            
            self.logger.info(f"Loaded image {image_path.name} into slot {slot_index + 1}")
            
        except Exception as e:
            self.logger.error(f"Failed to load image {image_path}: {e}")
    
    def _clear_image_grid(self):
        """Clear all images from the grid"""
        for i, label in enumerate(self.image_labels):
            label.clear()
            label.setText(f"Waiting for Image {i+1}...")
            label.setStyleSheet("""
                QLabel#image_placeholder {
                    border: 2px dashed #cccccc;
                    border-radius: 8px;
                    background-color: #f8f8f8;
                    color: #666666;
                    font-size: 14px;
                }
            """)
            
            # Disable buttons
            if i < len(self.image_slots):
                self.image_slots[i].download_btn.setEnabled(False)
                self.image_slots[i].pick_btn.setEnabled(False)
                self.image_slots[i].pick_btn.setStyleSheet("")  # Reset selection style
        
        # Clear tracking arrays
        self.image_paths = [None] * len(self.image_labels)
        self.selected_images.clear()