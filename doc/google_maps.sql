/*
 Navicat Premium Data Transfer

 Source Server         : google_maps
 Source Server Type    : MySQL
 Source Server Version : 80403
 Source Host           : vip3.xiaomiqiu123.top:56662
 Source Schema         : google_maps

 Target Server Type    : MySQL
 Target Server Version : 80403
 File Encoding         : 65001

 Date: 14/06/2025 14:52:35
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for business_records
-- ----------------------------
DROP TABLE IF EXISTS `business_records`;
CREATE TABLE `business_records`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `website` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL,
  `email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `phones` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL,
  `facebook` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL,
  `twitter` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL,
  `instagram` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL,
  `linkedin` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL,
  `whatsapp` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL,
  `youtube` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL,
  `created_at` timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP,
  `send_count` int(0) NULL DEFAULT 0,
  `updated_at` timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `email_unique`(`email`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1729 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for last_extraction_positions
-- ----------------------------
DROP TABLE IF EXISTS `last_extraction_positions`;
CREATE TABLE `last_extraction_positions`  (
  `id` int unsigned NOT NULL,
  `url` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `last_position` int(0) NULL DEFAULT NULL,
  `timestamp` timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unique_url`(`url`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 694 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
