--
-- PostgreSQL database dump
--

-- Dumped from database version 15.15 (Debian 15.15-1.pgdg13+1)
-- Dumped by pg_dump version 17.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: payments; Type: TABLE; Schema: public; Owner: stormy
--

CREATE TABLE public.payments (
    payment_id text NOT NULL,
    chat_id bigint,
    amount real,
    status text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.payments OWNER TO stormy;

--
-- Name: users; Type: TABLE; Schema: public; Owner: stormy
--

CREATE TABLE public.users (
    chat_id bigint NOT NULL,
    username text,
    vless_key text,
    expiry_date text,
    reminder_sent boolean DEFAULT false,
    gift_used boolean DEFAULT false,
    inbound_id integer,
    server_url text
);


ALTER TABLE public.users OWNER TO stormy;

--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: stormy
--

COPY public.payments (payment_id, chat_id, amount, status, created_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: stormy
--

COPY public.users (chat_id, username, vless_key, expiry_date, reminder_sent, gift_used, inbound_id, server_url) FROM stdin;
196880451	@Assia_G	vless://ca344ccc-4c91-4afd-baad-8043021af63d@38.135.53.154:10465?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=1e57ef65&spx=%2F#New-qypy6z4ck4nrnep9	26.12.2025 09:47	f	f	266	https://38.135.53.154:55555/v9y6CFQiVz
244408185	@negativy_to4ka_net	vless://82fff8f3-6fc1-4328-a85e-f8c1225bd1f5@38.135.53.215:14101?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=14842629&spx=%2F#New-6de306i458xp7mmq	30.01.2026 17:56	f	f	134	https://38.135.53.215:5278/XRp51tK8il0WdQ9
265196721	@Juliia_N	vless://f3045644-bbd2-49b2-aa7a-9425dfc469ef@38.135.53.215:38626?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=8bae89c6&spx=%2F#New-79irh4ddxg4inhl2	26.12.2025 09:53	f	f	57	https://38.135.53.215:5278/XRp51tK8il0WdQ9
288676817	@dannie_tsed	vless://64674c5a-f1f4-4345-885b-6ede1222c92f@38.135.53.154:11109?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=47144237&spx=%2F#New-7fm2jlmynn9bqp7g	29.01.2026 14:31	f	f	348	https://38.135.53.154:55555/v9y6CFQiVz
358207806	@roshkate	vless://3223df42-6a90-4912-b2fe-f94ce9b72566@38.135.53.215:25592?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=e050e8c5&spx=%2F#New-tknonx6iacpbrcxg	29.12.2025 15:06	f	f	102	https://38.135.53.215:5278/XRp51tK8il0WdQ9
397596157	@Valentina_Agarkova	vless://7d15e2fd-f674-41d9-9eac-358087d5777e@38.135.53.215:31415?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=eba26e95&spx=%2F#New-ujdai2klw4hc2497	18.12.2025 06:02	f	f	123	https://38.135.53.215:5278/XRp51tK8il0WdQ9
397835983	@Nikolai_p40	vless://ef8d74f4-9038-45b4-9896-fc05976c57f9@38.135.53.154:53062?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=63cdcad5&spx=%2F#New-6sddj0jypl2z97p3	31.01.2026 16:39	f	f	352	https://38.135.53.154:55555/v9y6CFQiVz
401924639	@Solo_Tu96	vless://99e5549f-3674-4da1-b7d7-94f6f4191720@38.135.53.215:44055?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=7ae99f6a&spx=%2F#New-7magd71j05i9lmcg	21.12.2025 12:18	f	f	124	https://38.135.53.215:5278/XRp51tK8il0WdQ9
412792458	Без username	vless://a8c9be9f-7484-4761-9fab-868fa4cd3ee6@38.135.53.154:50389?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=e97eafe5&spx=%2F#New-4q3mtq8peoe727op	30.01.2026 13:06	f	f	350	https://38.135.53.154:55555/v9y6CFQiVz
533802354	@july_razumova	vless://f3badabd-4fa3-4171-ad0d-f68c8beeef04@38.135.53.215:12097?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=d5a1d9f2&spx=%2F#New-g5qkw8a626m8qw67	29.12.2025 09:39	f	f	131	https://38.135.53.215:5278/XRp51tK8il0WdQ9
685367364	@Mariameteo	vless://e4bdc300-b61e-4909-b43e-2f56c64dc560@38.135.53.215:11964?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=f656d4dd&spx=%2F#New-8i4s1rlnubzjl5zy	15.01.2026 10:49	f	f	122	https://38.135.53.215:5278/XRp51tK8il0WdQ9
693473103	@margosshaa_k	vless://cd02e8ed-9949-4d68-97ae-7d9387523135@38.135.53.154:31494?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=de703b0b&spx=%2F#New-yjocada8g1kxgr0b	26.12.2025 09:57	f	f	298	https://38.135.53.154:55555/v9y6CFQiVz
717530017	@sultanova_vv	vless://e9ae702e-f28d-4e1c-b923-c71cf8bc7e86@38.135.53.154:55786?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=7c88c428&spx=%2F#New-d7i2ipv67g7n6f2a	29.01.2026 11:40	f	f	346	https://38.135.53.154:55555/v9y6CFQiVz
801912621	@puddddding7	vless://3dc59b75-942e-41fa-a713-0f7df9efc1e2@38.135.53.154:21852?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=111348db&spx=%2F#New-h4ya5wsvjhwhbtpx	26.12.2025 10:56	f	f	316	https://38.135.53.154:55555/v9y6CFQiVz
806641487	@aleksa306	vless://e2ccae38-58c4-4fcd-afb4-33ddc0e36694@38.135.53.154:57167?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=fe584a8a&spx=%2F#New-gvwlmhjyib0gugfj	01.01.2026 11:29	f	f	286	https://38.135.53.154:55555/v9y6CFQiVz
809789088	@eklkeklk	vless://a9f9e5ec-5b51-43e8-a009-b261dce09658@38.135.53.154:35375?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=fea807a3&spx=%2F#New-eyaj3o33vah2dwzj	22.12.2025 10:03	f	f	342	https://38.135.53.154:55555/v9y6CFQiVz
817461061	@kiracommerce	vless://a8823877-13db-45e6-a6a0-8ff44743203e@38.135.53.154:32459?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=b879e8f9&spx=%2F#New-5n3wnwlyjj0u891s	17.12.2025 13:14	f	f	340	https://38.135.53.154:55555/v9y6CFQiVz
827776464	Без username	vless://9e86aeb7-83a2-4ad0-bb63-e65336fb68c7@38.135.53.215:11268?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=0ec32b7e&spx=%2F#New-mnwyufkj9veu0ltm	03.12.2025 17:35	t	f	117	https://38.135.53.215:5278/XRp51tK8il0WdQ9
852063364	Без username	vless://abbc9554-b09c-4ddd-a808-a5f3933ed0ae@38.135.53.215:18347?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=48e99c77&spx=%2F#New-gp3f1il5scg7e9dh	26.12.2025 08:22	f	f	130	https://38.135.53.215:5278/XRp51tK8il0WdQ9
911348507	@Artemi_a_ne_artem	vless://cc4ed87b-f882-4d0e-b2b8-5270522b8b59@38.135.53.154:21594?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=a2934d5f&spx=%2F#New-ovflraz9c72y6dqj	13.09.2026 10:43	f	f	296	https://38.135.53.154:55555/v9y6CFQiVz
950866927	@Timofey1211	vless://eb192152-5615-4a70-a1d6-bfd7a4f5ba8c@38.135.53.154:28815?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=b4a2ef6b&spx=%2F#New-tw477zkal13ibepc	27.12.2025 11:21	f	f	328	https://38.135.53.154:55555/v9y6CFQiVz
960047946	@kraskoarina	vless://a03b3ab8-d78b-4ce1-a058-67f121057cd8@38.135.53.154:43005?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=328053b6&spx=%2F#New-75ba5iyjaoiur4ht	29.01.2026 15:23	f	f	349	https://38.135.53.154:55555/v9y6CFQiVz
983360115	@deadboy_hookah_sesh	vless://2686cb53-ee9b-4e42-a370-c93d3fc8362a@38.135.53.215:16283?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=a933997f&spx=%2F#New-96a8qc6nhgqcjhts	25.12.2025 10:49	f	f	126	https://38.135.53.215:5278/XRp51tK8il0WdQ9
1006241248	@mranilyam	vless://6d1b4558-b339-4848-b8de-e4e9888d328b@38.135.53.154:45233?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=7a912221&spx=%2F#New-t7etgn227kfaffk5	18.12.2025 14:51	f	f	341	https://38.135.53.154:55555/v9y6CFQiVz
1015504710	@Olga_Bak	vless://31966ef9-ea33-4b53-b2c6-5980d07f594d@38.135.53.215:23769?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=e1bcbc41&spx=%2F#New-74foh9v3hddjuyeu	25.12.2025 12:30	f	f	127	https://38.135.53.215:5278/XRp51tK8il0WdQ9
1019580316	@diana_shame	vless://810d85c6-7eca-4a91-bce0-169282cee4ec@38.135.53.154:32469?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=7ac58852&spx=%2F#New-xlbmpxqrq41mhlp2	29.01.2026 14:09	f	f	347	https://38.135.53.154:55555/v9y6CFQiVz
1040013169	@Kirill_Luzianin	vless://1c2905ed-a8a5-42f6-9cee-706ed37d3475@38.135.53.215:41938?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=2525abec&spx=%2F#New-fufnuxve5585j1oa	25.12.2025 19:22	f	f	129	https://38.135.53.215:5278/XRp51tK8il0WdQ9
1044005195	@m_iiiig	vless://cc030b77-61c3-4e61-88ce-e5ae63f42935@38.135.53.215:52927?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=858d634e&spx=%2F#New-6w78fl9jz1hu21ze	03.12.2025 13:28	t	f	116	https://38.135.53.215:5278/XRp51tK8il0WdQ9
1050409336	@raylinnie	vless://ab038f79-8358-4a44-a11a-9d99cf13e6fa@38.135.53.215:45011?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=5805fcf2&spx=%2F#New-lg2spq21j200ao9c	06.08.2026 14:47	f	f	76	https://38.135.53.215:5278/XRp51tK8il0WdQ9
1070585275	@hokkaido228	vless://8a7b2991-7794-48fa-8365-2c03a3ccd2a1@38.135.53.215:41412?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=6fc0fce2&spx=%2F#New-ls1v44r3m80cnexc	04.12.2025 06:27	f	f	118	https://38.135.53.215:5278/XRp51tK8il0WdQ9
1075196546	Без username	vless://a48efb52-889e-4bda-853a-c15fae916e95@38.135.53.154:38438?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=f9badd16&spx=%2F#New-i79c8izolgjzi9e7	23.12.2025 14:24	f	f	343	https://38.135.53.154:55555/v9y6CFQiVz
1150730884	Без username	vless://7699df9b-8386-45b3-ba52-f68bc89f96c8@38.135.53.215:33970?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=62ac16c3&spx=%2F#New-mnfskmxnfpnku94h	25.12.2025 15:35	f	f	128	https://38.135.53.215:5278/XRp51tK8il0WdQ9
1313616820	Без username	vless://42e65c59-ca7b-4e12-8903-fc101c301ee8@38.135.53.215:26916?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=88dff678&spx=%2F#New-00ktuki8ap9qb278	04.12.2025 16:03	f	f	119	https://38.135.53.215:5278/XRp51tK8il0WdQ9
1350269200	@Suleimanova_Elvina	vless://302c9bbd-057e-4eb8-99b2-759e9f502921@38.135.53.215:56424?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=128952f2&spx=%2F#New-kx58vi95lfotxkhb	06.12.2025 19:15	f	f	120	https://38.135.53.215:5278/XRp51tK8il0WdQ9
1423139361	Без username	vless://e6a23c50-2bb7-4cb9-92d2-ee97e90b63d7@38.135.53.154:27099?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=559f5377&spx=%2F#New-x9l9nub8cu19k4zs	23.12.2025 08:01	f	f	312	https://38.135.53.154:55555/v9y6CFQiVz
1439561399	Без username	vless://6ffd613e-f641-47d8-8a30-e1c450f6cede@38.135.53.215:53999?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=012c2283&spx=%2F#New-ingqxdxte44r3fou	01.01.2026 16:39	f	f	135	https://38.135.53.215:5278/XRp51tK8il0WdQ9
1503489614	@gerasenkova	vless://b3d4e013-bc17-453d-a4c7-c0a506188bae@38.135.53.215:59031?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=a89e56f1&spx=%2F#New-gh59uf6topgppkux	30.01.2026 13:05	f	f	133	https://38.135.53.215:5278/XRp51tK8il0WdQ9
1559034649	@murchik1984	vless://ac35f4cb-f632-4575-8e2c-c80188adcbe4@38.135.53.215:27517?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=8b10be83&spx=%2F#New-h07af7mbc83kd3th	25.12.2025 09:53	f	f	68	https://38.135.53.215:5278/XRp51tK8il0WdQ9
1585430841	@LenaBalid	vless://f77113f4-8e24-436a-9966-862fbdeb1daa@38.135.53.154:29142?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=dfb0c218&spx=%2F#New-uxjenkkzadbiuud2	08.12.2025 02:25	f	f	339	https://38.135.53.154:55555/v9y6CFQiVz
1626378585	Без username	vless://75767a7c-1057-44f8-8371-e0d902267d50@38.135.53.215:54090?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=7118b693&spx=%2F#New-lqvmrdewrm1961km	23.12.2025 14:44	f	f	125	https://38.135.53.215:5278/XRp51tK8il0WdQ9
1681246178	@nastyvasy	vless://1e6350e8-7ff6-4c6e-ae3a-5a8c0720c949@38.135.53.215:20455?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=2554de57&spx=%2F#New-0ufffdbkvxuiolrt	02.03.2026 17:08	f	f	132	https://38.135.53.215:5278/XRp51tK8il0WdQ9
1694692368	@DashaLuzyanina	vless://c0ca493b-869d-4afa-8e91-9ba776e2f994@38.135.53.154:50399?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=f568bd04&spx=%2F#New-4santmd3ff8l3omn	26.12.2025 12:15	f	f	344	https://38.135.53.154:55555/v9y6CFQiVz
1713941651	@ChestAuto_NN	vless://f9fbcb9e-64c9-470f-8614-85b361002493@38.135.53.154:46366?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=2389f68c&spx=%2F#New-8vnd05vztty6de62	04.12.2025 03:21	f	f	336	https://38.135.53.154:55555/v9y6CFQiVz
1772395192	Без username	vless://eaf63cd1-70ca-4589-bb07-82fb86cc5b2a@38.135.53.154:30390?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=f5d2d5f0&spx=%2F#New-66f4f4n3x6e082n8	04.12.2025 10:55	f	f	337	https://38.135.53.154:55555/v9y6CFQiVz
1823418070	@a3848839	vless://3bb54197-32af-4c87-9864-95beb6d4606d@38.135.53.215:31803?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=d5a9a7ee&spx=%2F#New-kkryklo225l33ukf	20.12.2025 11:43	f	f	108	https://38.135.53.215:5278/XRp51tK8il0WdQ9
1896111727	Без username	vless://5d8a6b7f-54a0-4849-9e67-c01d3fc6468b@38.135.53.215:40657?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=725edc15&spx=%2F#New-ksf52xbzkyztthwn	08.12.2025 11:48	f	f	121	https://38.135.53.215:5278/XRp51tK8il0WdQ9
1902290413	@hirakiri_shogun	vless://24d3b34d-8212-4576-8dc7-2b76fdf05acd@38.135.53.215:55935?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=85d4110e&spx=%2F#New-46kvyxfeg7188724	17.08.2026 10:32	f	f	72	https://38.135.53.215:5278/XRp51tK8il0WdQ9
1930001088	@irinamoet	vless://d147d3c4-26ed-4625-9867-9f40eb7fc618@38.135.53.154:14380?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=fbd21ac0&spx=%2F#New-b0q1435crr7bm4ew	22.12.2025 07:02	f	f	311	https://38.135.53.154:55555/v9y6CFQiVz
5210600987	@klim_kob	vless://9ad6d6de-ead1-4454-b39e-0e20b11173bd@38.135.53.154:45056?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=19e594b3&spx=%2F#New-vmzn8znjb423vnsi	04.12.2025 15:38	f	f	324	https://38.135.53.154:55555/v9y6CFQiVz
6940768968	Без username	vless://88fb5e34-6322-436e-9d1b-c337a6e6c78a@38.135.53.154:52287?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=0466719d&spx=%2F#New-iesxx3pnivfbkdbs	27.12.2025 17:10	f	f	345	https://38.135.53.154:55555/v9y6CFQiVz
7530633498	Без username	vless://d3a344c9-fdff-4a36-9055-186caab63f9b@38.135.53.154:29343?type=tcp&security=reality&pbk=2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk&fp=random&sni=yahoo.com&sid=9bc5cb8f&spx=%2F#New-2hwflf3sc52lf8eg	05.12.2025 08:03	f	f	338	https://38.135.53.154:55555/v9y6CFQiVz
\.


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: stormy
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (payment_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: stormy
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (chat_id);


--
-- PostgreSQL database dump complete
--

