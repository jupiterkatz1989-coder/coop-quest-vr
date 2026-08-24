import {chromium} from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
const root=path.resolve(import.meta.dirname,'..'),shots=path.join(root,'screenshots'),url=process.env.TEST_URL??'http://127.0.0.1:8800/coop-quest-vr/'
fs.mkdirSync(shots,{recursive:true})
const browser=await chromium.launch({headless:true}),errors=[]
const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1})
page.on('pageerror',e=>errors.push(String(e)))
page.on('console',m=>{if(m.type()==='error')errors.push(m.text())})
await page.goto(url,{waitUntil:'networkidle'});await page.getByText(/experiencias cooperativas/).waitFor()
const totalText=await page.getByText(/experiencias cooperativas/).textContent()
const initialCards=await page.locator('.card').count(),desktopOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth)
await page.screenshot({path:path.join(shots,'public-desktop.png'),fullPage:true})
await page.locator('label:has-text("Tipo de plataforma") select').selectOption('pcvr')
await page.locator('label:has-text("Reseñas mínimas") select').selectOption('100')
const filteredText=await page.locator('.result-bar strong').textContent()
await page.getByRole('button',{name:'Limpiar'}).click();await page.locator('.card-main').first().click();await page.getByRole('dialog').waitFor();await page.getByRole('button',{name:'Cerrar'}).click()
await page.setViewportSize({width:390,height:844});await page.goto(url,{waitUntil:'networkidle'});await page.getByText(/experiencias cooperativas/).waitFor()
const mobileOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth)
await page.screenshot({path:path.join(shots,'public-mobile.png'),fullPage:true})
const result={title:await page.title(),url:page.url(),totalText,initialCards,filteredText,desktopOverflow,mobileOverflow,pageErrors:errors,screenshots:['public-desktop.png','public-mobile.png']}
fs.writeFileSync(path.join(shots,'browser_verification.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));await browser.close()
